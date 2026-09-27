# to compress vid
```bash
ffmpeg -i yogii_velachery.mp4 -r 25 -c:v libx264 -preset slow -crf 27 -pix_fmt yuv420p -an compressed_anpr.mp4
```
