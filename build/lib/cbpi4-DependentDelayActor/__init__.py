# -*- coding: utf-8 -*-
import logging
import asyncio
from cbpi.api import *

logger = logging.getLogger(__name__)

@parameters([
    Property.Actor(label="TargetActor", description="Select the actor which should be switched after the dependency is fulfilled."),
    Property.Actor(label="DependencyActor", description="Select the actor which must have the required state before TargetActor is switched."),
    Property.Select(label="RequiredState", options=["ON", "OFF"], description="Required state of DependencyActor before TargetActor is switched."),
    Property.Select(label="AutoSwitchDependency", options=["Yes", "No"], description="Switch DependencyActor automatically to RequiredState if needed."),
    Property.Number(label="Delay", configurable=True, description="Delay in seconds after DependencyActor is in RequiredState before TargetActor is switched."),
    Property.Select(label="ResetDependencyOnOff", options=["No", "Yes"], description="Switch DependencyActor to opposite state when this actor is switched off.")
])
class DependentDelayActor(CBPiActor):

    async def on_start(self):
        self.state = False
        self.power = 100
        self.target_actor = self.props.get("TargetActor", None)
        self.dependency_actor = self.props.get("DependencyActor", None)
        self.required_state = self.props.get("RequiredState", "ON")
        self.auto_switch = self.props.get("AutoSwitchDependency", "Yes")
        self.reset_dependency = self.props.get("ResetDependencyOnOff", "No")
        try:
            self.delay = float(self.props.get("Delay", 0))
        except Exception:
            self.delay = 0
        logging.info("DEPENDENT DELAY ACTOR STARTED")
        pass

    def get_state(self):
        return self.state

    def dependency_state_is_required(self):
        try:
            actor = self.cbpi.actor.find_by_id(self.dependency_actor)
            current_state = actor.instance.state
        except Exception:
            current_state = False
        required = True if self.required_state == "ON" else False
        return current_state == required

    async def switch_dependency_to_required(self):
        if self.dependency_actor is None:
            return True
        if self.dependency_state_is_required():
            return True
        if self.auto_switch != "Yes":
            return False
        if self.required_state == "ON":
            await self.cbpi.actor.on(self.dependency_actor, 100)
        else:
            await self.cbpi.actor.off(self.dependency_actor)
        return True

    async def on(self, power=None):
        if power is not None:
            self.power = power
        else:
            self.power = 100
        if self.target_actor is None:
            self.state = False
            return
        ok = await self.switch_dependency_to_required()
        if ok is False:
            self.state = False
            return
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if self.dependency_actor is not None and self.dependency_state_is_required() is False:
            self.state = False
            return
        await self.cbpi.actor.on(self.target_actor, self.power)
        self.state = True
        await self.cbpi.actor.ws_actor_update()

    async def off(self):
        if self.target_actor is not None:
            await self.cbpi.actor.off(self.target_actor)
        if self.reset_dependency == "Yes" and self.dependency_actor is not None:
            if self.required_state == "ON":
                await self.cbpi.actor.off(self.dependency_actor)
            else:
                await self.cbpi.actor.on(self.dependency_actor, 100)
        self.state = False
        await self.cbpi.actor.ws_actor_update()

    async def run(self):
        while self.running:
            await asyncio.sleep(1)
        pass

    async def set_power(self, power):
        self.power = power
        if self.target_actor is not None:
            await self.cbpi.actor.set_power(self.target_actor, self.power)
        pass


def setup(cbpi):
    cbpi.plugin.register("Dependent Delay Actor", DependentDelayActor)
    pass
