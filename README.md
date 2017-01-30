#Termux-Mpv

This is a wrapper for mpv on [Termux](termux.net). It displays a notification with media controls

![Screenshot](/Screenshots/Notification-Media-Controls.png)

## Requirements

* [Termux:API](https://play.google.com/store/apps/details?id=com.termux.api) App from Google Play 

### Packages: 

* `termux-api`
* `python`
* `mpv`
```
apt install termux-api python mpv
```

## Installation

```
pip install git+https://github.com/Neo-Oli/Termux-Mpv
```

## Usage

`termux-mpv` is a drop-in replacement for `mpv`. All arguments get forwarded to mpv.
