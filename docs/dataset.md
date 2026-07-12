# Dataset Documentation

## Overview

This document defines the organization, structure, naming conventions, and metadata for all datasets used in the TennisLabAI project.

The objective is to ensure consistency, reproducibility, and traceability throughout the data lifecycle.

---

# 1. Dataset Objectives

The dataset is designed to:

* Store synchronized multimodal measurements.
* Support reproducible biomechanical research.
* Enable machine learning experiments.
* Facilitate comparison between wearable sensing and markerless computer vision.

---

# 2. Data Modalities

The framework integrates multiple data sources.

## Wearable IMU

Examples:

* Segment orientation
* Linear acceleration
* Angular velocity

---

## RGB Video

Examples:

* Single-camera recordings
* Multi-camera recordings
* High-speed recordings (optional)

---

## Metadata

Examples:

* Participant information
* Trial information
* Experimental conditions
* Equipment configuration

---

## OpenSim Outputs

Examples:

* Joint moments
* Joint reaction forces
* Muscle forces
* Muscle activations

---

## Machine Learning Features

Examples:

* Pose features
* IMU-derived features
* Fused biomechanical features

---

# 3. Dataset Organization

```text
data/

├── raw/
│   ├── imu/
│   ├── video/
│   └── metadata/
│
├── processed/
│   ├── synchronized/
│   ├── kinematics/
│   ├── features/
│   └── simulations/
│
├── annotations/
│
├── benchmarks/
│
└── external/
```

---

# 4. Participant Structure

Each participant should have a unique anonymous identifier.

Example:

Participant IDs

P001

P002

P003

...

---

# 5. Session Structure

Each recording session should include:

* Session ID
* Date
* Participant ID
* Experimental setup
* Notes

Example

S001

S002

---

# 6. Trial Structure

Each movement repetition is stored as an independent trial.

Example

Trial 01

Trial 02

Trial 03

Each trial should reference:

* Participant
* Session
* Tennis task

---

# 7. Tennis Tasks

Supported tasks may include:

* Flat Serve
* Slice Serve
* Kick Serve
* Forehand
* Backhand
* Volley
* Ready Position

Additional tasks may be added.

---

# 8. File Naming Convention

Recommended format:

ParticipantID_Task_Session_Trial

Example:

P001_Forehand_S01_T03

P005_FlatServe_S02_T08

This naming convention should be used consistently across all data modalities.

---

# 9. Metadata Fields

Each recording should include:

Participant Information

* Participant ID
* Age
* Height
* Weight
* Dominant hand
* Playing experience

Experimental Information

* Date
* Tennis task
* Trial number
* Camera configuration
* IMU configuration

Recording Parameters

* IMU sampling frequency
* Camera frame rate
* Recording duration

---

# 10. Data Quality

Each recording should be checked for:

* Missing frames
* Sensor drift
* Synchronization errors
* Sensor displacement
* Recording artifacts

Low-quality recordings should be documented.

---

# 11. Versioning

Dataset versions should be tracked.

Example

Version 0.1

Pilot recordings

Version 0.2

First experimental dataset

Version 1.0

Publication-ready dataset

---

# 12. Privacy

Participant identities should never appear in public datasets.

Personal information must remain confidential.

Only anonymous participant identifiers should be used.

---

# 13. Future Extensions

The dataset structure is designed to support future additions, including:

* EMG
* Force plates
* Pressure insoles
* Wearable robotics
* Additional sports
* Clinical movement analysis

