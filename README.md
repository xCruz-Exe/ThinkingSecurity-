# Thinking Security - Website Protection Engine

Thinking Security is a high-performance security reverse proxy designed to safeguard your web applications against modern threats. Built with a focus on simplicity and efficiency, it acts as a robust shield, filtering malicious traffic before it ever reaches your origin server.

> [!NOTE]
> This project was created for educational purposes and personal interest in web security. I am not a professional expert in this field, and this tool is built as a learning experiment. Please feel free to provide feedback or suggestions for improvement!

## Why Thinking Security?
In today's web, security is paramount. Thinking Security provides a multi-layered defense strategy:
- **Stealth Mode**: Hides your real server IP from the public web.
- **Intelligent Filtering**: Deeply inspects requests for common attack patterns (SQLi, XSS, RCE).
- **Automated Mitigation**: Automatically challenges suspicious behavior to block botnets.

## Features
- **Origin Hiding**: Stop hackers from finding your real server IP.
- **Advanced WAF**: Protection against SQLi, XSS, RCE, and Path Traversal.
- **Botnet Mitigation**: JavaScript-based challenge to block automated bots.
- **Dynamic Rate Limiting**: Prevent volumetric DDoS attacks.
- **Anomaly Detection**: Auto-blocks IPs that perform directory brute-forcing.

## Setup
1. Edit `config.yaml` and set `target_url` to your real website URL.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Start Thinking Security:
   ```bash
   python main.py
   ```

---
Made with ❤️ for learning and security!
4. Point your domain DNS to the ShieldProxy server IP.

## Configuration
- `listen_port`: The port ShieldProxy will listen on (default: 8080).
- `sensitivity`: How aggressive the WAF is (1-10).
- `js_challenge_enabled`: Enable/Disable the anti-bot challenge.
