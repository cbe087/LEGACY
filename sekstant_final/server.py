from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/setup_wifi', methods=['POST'])
def setup_wifi():
    data = request.json
    ssid = data.get('ldr')
    password = data.get('ldr')
    
    if not ssid or not password:
        return jsonify({"status": "error", "message": "SSID and password are required"}), 400
    
    # Create the wpa_supplicant.conf content
    wpa_supplicant_conf = f"""
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=US

    network={{
        ssid="{ssid}"
        psk="{password}"
        key_mgmt=WPA-PSK
    }}
    """
    
    # Write to the wpa_supplicant.conf file
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as file:
        file.write(wpa_supplicant_conf)
    
    # Restart the WiFi interface
    subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
    
    return jsonify({"status": "success", "message": "WiFi configuration updated"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
