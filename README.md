# cbpi4-DependentDelayActor

CraftBeerPi4 actor plugin for switching up to two main actors after dependency actors have reached configurable states and an optional delay has finished.

## Features

- Up to 2 main actors
- Up to 2 dependency actors
- Configurable ON/OFF dependency states
- Automatic dependency switching
- Configurable delay in seconds
- CraftBeerPi dashboard notifications, if supported by the installed CBPi version
- Delay cancellation when the actor is switched off before the delay ends

## Actor type

After installation, create an actor with type:

**Dependent Delay Actor**

## Configuration

| Setting | Description |
|---|---|
| MainActor1 | First main actor switched after dependency checks and delay |
| MainActor2 | Optional second main actor |
| DependencyActor1 | First dependency actor |
| DependencyState1 | Required state for dependency actor 1: ON or OFF |
| DependencyActor2 | Optional second dependency actor |
| DependencyState2 | Required state for dependency actor 2: ON or OFF |
| AutoSwitchDependencies | Automatically switch dependencies to their required state |
| Delay | Delay in seconds before the main actor(s) are switched |
| ResetDependenciesOnOff | Switch dependency actors to the opposite state when this actor is switched off |
| Notifications | Show dashboard notifications if available in your CraftBeerPi installation |

## Installation from GitHub on Raspberry Pi

```bash
git clone git@github.com:gerrywin/cbpi4-DependentDelayActor.git
cd cbpi4-DependentDelayActor
pip3 install . --break-system-packages
```

Restart CraftBeerPi afterwards:

```bash
sudo systemctl restart craftbeerpi
```

If your service has a different name, try:

```bash
sudo systemctl restart cbpi
```

## Update on Raspberry Pi

```bash
cd ~/cbpi4-DependentDelayActor
git pull
pip3 install . --break-system-packages
sudo systemctl restart craftbeerpi
```

## First GitHub upload

Use SSH, not HTTPS, so GitHub does not ask for username and password:

```bash
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin git@github.com:gerrywin/cbpi4-DependentDelayActor.git
git push -u origin main
```

If `origin` already exists with an HTTPS URL, change it to SSH:

```bash
git remote set-url origin git@github.com:gerrywin/cbpi4-DependentDelayActor.git
git push -u origin main
```

## License

GPLv3
