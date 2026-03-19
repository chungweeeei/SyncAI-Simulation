# Examples

## Image Capture

Capture an image from a ROS 2 topic and save to `artifacts/`:

```bash
python3 scripts/ros2_cli.py topics capture-image \
  --topic /camera/image_raw/compressed \
  --output test.jpg \
  --timeout 5 \
  --type auto
```

Requires `opencv-python` and `numpy`.

---

## Discord Integration

Send a captured image to a Discord channel:

```bash
python3 scripts/discord_tools.py send-image \
  --path artifacts/test.jpg \
  --channel-id 123456789012345678 \
  --config ~/.nanobot/config.json \
  --delete
```

Requires `requests` and a bot token in `~/.nanobot/config.json`. See [`SKILL.md`](SKILL.md) for the expected config file format.
