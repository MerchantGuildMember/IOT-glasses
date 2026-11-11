# Architecture

## Now (checkpoint prototype)

```mermaid
flowchart LR
    subgraph Pi["Raspberry Pi 4 (the glasses)"]
        BTN[Enter key / button] --> CAM[Camera or sample image]
        TOF[VL53L0X distance] --> LED[Alert LED]
        DHT[DHT22 temp/humidity]
        SPK[Speaker via espeak-ng]
    end
    subgraph Server["FastAPI server (on my PC for now)"]
        API["/api/capture<br/>device token"]
        DASH["Dashboard<br/>login required"]
    end
    LLM["LLM<br/>LM Studio (local) or Claude API"]
    CARER([Carer in a browser])

    CAM -- "photo over HTTP" --> API
    API -- image --> LLM
    LLM -- short description --> API
    API -- description --> SPK
    DASH -- "image, status, description" --> CARER
```

1. The user presses capture on the Pi. The Pi takes a photo, or uses a saved one until the camera arrives.
2. The Pi uploads the photo to the server with a secret device token.
3. The server sends the image to the LLM. The dashboard shows "Sending to LLM..." and then "LLM responding...".
4. The description comes back. The dashboard shows it, and the Pi reads it out loud.

The LLM API key lives only on the server, never on the Pi.

## Final target (what the brief asks for)

```mermaid
flowchart LR
    Pi[Raspberry Pi 4] -- "HTTPS: image upload" --> Nginx
    Pi <-- "pub-sub (TLS, access-controlled channels):<br/>sensor readings up, descriptions down" --> PS[(Pub-sub service)]
    PS <--> App
    subgraph AWS["AWS EC2, custom HTTPS domain"]
        Nginx[Nginx reverse proxy + TLS] --> App[FastAPI app]
        App --> DB[(Database, encrypted at rest)]
    end
    App --> LLM[LLM API]
    Browser([Carer browser]) -- "HTTPS + login" --> Nginx
```

Still to do for the final submission:
- Pub-sub for sensor readings (distance, temperature, humidity) and for sending descriptions back to the Pi
- A database for captures, descriptions and readings, with password hashing and encryption at rest
- Deployment to AWS behind Nginx on a custom HTTPS domain, without default server configs
- A Fritzing sketch, the screencast, and AI_Chat_Log.md
