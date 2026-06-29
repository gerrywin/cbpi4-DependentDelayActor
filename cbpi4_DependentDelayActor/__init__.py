# -*- coding: utf-8 -*-
"""CraftBeerPi4 Dependent Delay Actor.

Features:
- up to 2 main actors
- up to 2 dependency actors
- configurable dependency states ON/OFF
- automatic dependency switching
- configurable delay
- dashboard notifications, if supported by the installed CBPi version
"""

import asyncio
import logging
from cbpi.api import *

logger = logging.getLogger(__name__)


def _as_bool(value):
    return str(value).upper() == "ON"


@parameters([
    Property.Actor(label="MainActor1", description="First actor which should be switched after all dependencies are fulfilled."),
    Property.Actor(label="MainActor2", description="Optional second actor which should be switched after all dependencies are fulfilled."),
    Property.Actor(label="DependencyActor1", description="First dependency actor. Leave empty if not needed."),
    Property.Select(label="DependencyState1", options=["ON", "OFF"], description="Required state for DependencyActor1."),
    Property.Actor(label="DependencyActor2", description="Optional second dependency actor. Leave empty if not needed."),
    Property.Select(label="DependencyState2", options=["ON", "OFF"], description="Required state for DependencyActor2."),
    Property.Select(label="AutoSwitchDependencies", options=["Yes", "No"], description="Automatically switch dependency actors to their required states."),
    Property.Number(label="Delay", configurable=True, description="Delay in seconds after dependencies are fulfilled before main actors are switched."),
    Property.Select(label="ResetDependenciesOnOff", options=["No", "Yes"], description="Switch dependency actors to the opposite required state when this actor is switched off."),
    Property.Select(label="Notifications", options=["Yes", "No"], description="Show CraftBeerPi dashboard notifications when possible.")
])
class DependentDelayActor(CBPiActor):

    async def on_start(self):
        self.state = False
        self.power = 100
        self._task = None

        # Backward compatible fallback names from the first version
        self.main_actor_1 = self.props.get("MainActor1") or self.props.get("TargetActor")
        self.main_actor_2 = self.props.get("MainActor2")

        self.dependency_actor_1 = self.props.get("DependencyActor1") or self.props.get("DependencyActor")
        self.dependency_state_1 = self.props.get("DependencyState1") or self.props.get("RequiredState", "ON")
        self.dependency_actor_2 = self.props.get("DependencyActor2")
        self.dependency_state_2 = self.props.get("DependencyState2", "ON")

        self.auto_switch_dependencies = self.props.get("AutoSwitchDependencies") or self.props.get("AutoSwitchDependency", "Yes")
        self.reset_dependencies = self.props.get("ResetDependenciesOnOff") or self.props.get("ResetDependencyOnOff", "No")
        self.notifications = self.props.get("Notifications", "Yes")

        try:
            self.delay = max(0, float(self.props.get("Delay", 0)))
        except Exception:
            self.delay = 0

        logger.info("Dependent Delay Actor started")

    def get_state(self):
        return self.state

    def _is_configured(self, actor_id):
        return actor_id is not None and str(actor_id).strip() not in ["", "None", "0"]

    def _get_actor_state(self, actor_id):
        try:
            actor = self.cbpi.actor.find_by_id(actor_id)
            return bool(actor.instance.state)
        except Exception as e:
            logger.warning("Could not read actor state for %s: %s", actor_id, e)
            return None

    async def _notify(self, message, title="Dependent Delay Actor", notification_type="info"):
        logger.info("%s: %s", title, message)
        if self.notifications != "Yes":
            return

        # CBPi notification APIs differ between installations/plugins.
        # Try the common variants without failing the actor if none is available.
        try:
            notify = getattr(self.cbpi, "notify", None)
            if notify is not None:
                if hasattr(notify, "send_message"):
                    result = notify.send_message(title, message, notification_type)
                    if asyncio.iscoroutine(result):
                        await result
                    return
                if callable(notify):
                    result = notify(title, message, notification_type)
                    if asyncio.iscoroutine(result):
                        await result
                    return
        except Exception as e:
            logger.debug("Dashboard notification failed: %s", e)

        try:
            await self.cbpi.actor.ws_actor_update()
        except Exception:
            pass

    def _dependencies(self):
        deps = []
        if self._is_configured(self.dependency_actor_1):
            deps.append((self.dependency_actor_1, self.dependency_state_1))
        if self._is_configured(self.dependency_actor_2):
            deps.append((self.dependency_actor_2, self.dependency_state_2))
        return deps

    def _main_actors(self):
        actors = []
        if self._is_configured(self.main_actor_1):
            actors.append(self.main_actor_1)
        if self._is_configured(self.main_actor_2):
            actors.append(self.main_actor_2)
        return actors

    def _dependency_has_required_state(self, actor_id, required_state):
        current_state = self._get_actor_state(actor_id)
        if current_state is None:
            return False
        return current_state == _as_bool(required_state)

    async def _switch_dependency_to_required(self, actor_id, required_state):
        if self._dependency_has_required_state(actor_id, required_state):
            return True

        if self.auto_switch_dependencies != "Yes":
            return False

        if _as_bool(required_state):
            await self.cbpi.actor.on(actor_id, 100)
        else:
            await self.cbpi.actor.off(actor_id)

        await asyncio.sleep(0.2)
        return self._dependency_has_required_state(actor_id, required_state)

    async def _ensure_dependencies(self):
        for actor_id, required_state in self._dependencies():
            ok = await self._switch_dependency_to_required(actor_id, required_state)
            if not ok:
                await self._notify(
                    "Dependency actor %s is not in required state %s." % (actor_id, required_state),
                    notification_type="warning"
                )
                return False
        return True

    async def _switch_main_actors_on(self):
        main_actors = self._main_actors()
        if len(main_actors) == 0:
            await self._notify("No main actor configured.", notification_type="warning")
            return False

        for actor_id in main_actors:
            await self.cbpi.actor.on(actor_id, self.power)
        return True

    async def _run_on_sequence(self):
        try:
            if not await self._ensure_dependencies():
                self.state = False
                await self.cbpi.actor.ws_actor_update()
                return

            if self.delay > 0:
                await self._notify("Dependencies fulfilled. Waiting %.1f seconds." % self.delay)
                await asyncio.sleep(self.delay)

            # Re-check after delay, because dependencies may have changed while waiting.
            if not await self._ensure_dependencies():
                self.state = False
                await self.cbpi.actor.ws_actor_update()
                return

            if await self._switch_main_actors_on():
                self.state = True
                await self._notify("Main actor(s) switched on.")
            else:
                self.state = False

            await self.cbpi.actor.ws_actor_update()
        except asyncio.CancelledError:
            await self._notify("Switch-on sequence cancelled.")
            raise
        except Exception as e:
            self.state = False
            logger.exception("Dependent Delay Actor failed")
            await self._notify("Error: %s" % e, notification_type="danger")
            try:
                await self.cbpi.actor.ws_actor_update()
            except Exception:
                pass

    async def on(self, power=None):
        self.power = power if power is not None else 100

        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._task = asyncio.create_task(self._run_on_sequence())

    async def off(self):
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        for actor_id in self._main_actors():
            await self.cbpi.actor.off(actor_id)

        if self.reset_dependencies == "Yes":
            for actor_id, required_state in self._dependencies():
                if _as_bool(required_state):
                    await self.cbpi.actor.off(actor_id)
                else:
                    await self.cbpi.actor.on(actor_id, 100)

        self.state = False
        await self._notify("Main actor(s) switched off.")
        await self.cbpi.actor.ws_actor_update()

    async def run(self):
        while self.running:
            await asyncio.sleep(1)

    async def set_power(self, power):
        self.power = power
        for actor_id in self._main_actors():
            try:
                await self.cbpi.actor.set_power(actor_id, self.power)
            except Exception as e:
                logger.warning("Could not set power for actor %s: %s", actor_id, e)


def setup(cbpi):
    cbpi.plugin.register("Dependent Delay Actor", DependentDelayActor)
