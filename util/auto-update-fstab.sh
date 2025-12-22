#!/usr/bin/bash

FSTAB="/etc/fstab"
BACKUP="/etc/fstab.$(date +%F-%H%M%S).bak"

FS_MNT="/mnt/..."
FS_NEW_IP=""
FS_OLD_IP=""
FS_OLD_HOSTNAME=""

OLD_USR=""
NEW_USR=""
OLD_PWD=""
NEW_PWD=""

echo "Making backup of /etc/fstab"
cp "$FSTAB" "$BACKUP"

# Update existing entries in fstab
echo "Updating existing fstab entries"
sudo sed -i "s/${FS_OLD_IP}/${FS_NEW_IP}/g" "$FSTAB"
sudo sed -i "s/${FS_OLD_HOSTNAME}/${FS_NEW_IP}/g" "$FSTAB"

if [ -n "$NEW_USR" ] && [ -n "$NEW_PWD" ]; then
    # Update user credentials
    echo "Updating user credentials"
    sudo sed -i "s/username=${OLD_USR}/username=${NEW_USR}/g" "$FSTAB"
    sudo sed -i "s/password=${OLD_PWD}/password=${NEW_PWD}/g" "$FSTAB"
fi

echo "Updating stray entries"
sudo sed -i "s/192.168.0/172.16.1/g" "$FSTAB"