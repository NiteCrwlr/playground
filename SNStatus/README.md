# SNStatus.py

This script sends a broadcast message to your local LAN  
to find any Snapmaker 2.0 devices.  
It will then report IP-Address, Device Type and Status (IDLE/RUNNING)  

You can use this for your Home Assistant integration as example.  
It does not need any login to your Snapmaker.


# SNStatusV2.py

This is a new version, getting awesome more infos from Snapmaker API.   
See: https://community.home-assistant.io/t/adding-snapmaker-to-ha-need-help-on-making-udp-updatable-sensors/655036/12?u=guybrush_t  

Update 13.04.2024: To prevent locking of the Touchscreen,  
it will now report the full work progress only if the state is not IDLE.

