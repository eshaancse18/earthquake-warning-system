# Earthquake Warning System

This project is a software re-implementation of an existing Earthquake Warning
System that I worked on during my internship at CSIR-Central Scientific
Instruments Organisation (CSIR-CSIO), Chandigarh.

The original system was based on a Windows/C# setup. I worked on moving the
software to a modular Python/Linux architecture that can run on Raspberry Pi
CM4-based seismic sensing nodes.

## What the system does

The system continuously reads data from a seismic sensor and processes it on
the sensing node. When the data satisfies the event detection conditions, the
system records the event data and sends the required information to a Central
Receiving Station (CRS).

The main parts of the system are:

- Sensor data acquisition
- Signal processing and filtering
- Earthquake/event detection
- Pre-event and post-event data capture
- Station health monitoring
- Data logging
- GPS/time synchronization
- Communication with the CRS

## Basic Architecture

```text
ADXL345 Sensor
      |
      v
Raspberry Pi CM4
      |
      +--> Data Acquisition
      |
      +--> Signal Processing
      |
      +--> Event Detection
      |
      +--> Waveform Buffer
      |
      +--> Health Monitoring
      |
      +--> Local Storage
      |
      v
Central Receiving Station
      |
      v
Database / Event Storage
