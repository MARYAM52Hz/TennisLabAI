# Project Roadmap

## Overview

This roadmap outlines the planned evolution of the TennisLabAI project from the initial research concept to a complete multimodal biomechanics framework.

The roadmap is organized into research-oriented milestones rather than software-only tasks. Each phase represents a scientific objective that contributes to the overall vision of the project.

---

# Vision

Develop an open, reproducible, and modular framework for multimodal tennis biomechanics by integrating wearable sensing, markerless computer vision, musculoskeletal simulation, and artificial intelligence.

---

# Phase 0 — Project Foundation

## Objectives

* Define research scope
* Create GitHub repository
* Establish documentation
* Design project architecture

### Deliverables

* Repository structure
* README
* Documentation
* Research questions
* Experimental protocol
* Dataset design

### Status

Completed

---

# Phase 1 — Literature Review

## Objectives

Review the current state of the art in:

* Tennis biomechanics
* Wearable IMUs
* Markerless motion capture
* Sensor fusion
* OpenSim
* AI for sports analytics

### Deliverables

* Literature summaries
* Research gaps
* Design decisions

### Status

In Progress

---

# Phase 2 — Experimental Design

## Objectives

Design a reproducible laboratory protocol.

Tasks include:

* Participant recruitment criteria
* Sensor placement
* Camera placement
* Calibration procedure
* Synchronization strategy
* Ethical considerations

### Deliverables

* Experimental protocol
* Pilot experiment

### Status

Planned

---

# Phase 3 — Data Acquisition

## Objectives

Collect synchronized multimodal datasets.

Data sources include:

* Noraxon Ultium myoMOTION IMUs
* RGB video
* Experimental metadata

### Deliverables

* Raw dataset
* Metadata
* Quality assessment

### Status

Planned

---

# Phase 4 — Data Processing

## Objectives

Develop preprocessing pipelines.

Tasks include:

* IMU preprocessing
* Video preprocessing
* Synchronization
* Feature extraction

### Deliverables

* Clean datasets
* Processed features

### Status

Planned

---

# Phase 5 — Markerless Motion Capture

## Objectives

Develop and evaluate computer vision pipelines.

Potential frameworks:

* RTMPose
* MediaPipe
* OpenCap

### Deliverables

* Pose estimation models
* Kinematic outputs
* Validation reports

### Status

Planned

---

# Phase 6 — Sensor Fusion

## Objectives

Integrate IMU and vision-based measurements.

Potential methods:

* Kalman Filter
* Extended Kalman Filter
* Deep Learning Fusion
* Transformer-based fusion

### Deliverables

* Fused kinematic estimates
* Fusion evaluation

### Status

Planned

---

# Phase 7 — Musculoskeletal Simulation

## Objectives

Estimate biomechanical variables using OpenSim.

Potential outputs:

* Joint moments
* Joint reaction forces
* Muscle forces
* Muscle activations

### Deliverables

* OpenSim pipeline
* Simulation reports

### Status

Planned

---

# Phase 8 — Machine Learning

## Objectives

Develop AI models for biomechanical analysis.

Potential applications:

* Stroke classification
* Performance evaluation
* Technique assessment
* Injury risk prediction

Candidate models include:

* Random Forest
* XGBoost
* LSTM
* Transformers
* Graph Neural Networks

### Deliverables

* Trained models
* Performance evaluation
* Explainability analysis

### Status

Planned

---

# Phase 9 — Validation and Benchmarking

## Objectives

Compare the proposed framework with laboratory-grade measurements.

Evaluation metrics include:

* RMSE
* MAE
* Pearson correlation
* Intraclass Correlation Coefficient (ICC)
* Bland–Altman analysis

### Deliverables

* Statistical analysis
* Benchmark reports
* Comparative study

### Status

Planned

---

# Phase 10 — Scientific Dissemination

## Objectives

Share research outcomes with the scientific community.

Potential outputs include:

* Conference papers
* Journal publications
* Open datasets
* Open-source software
* Reproducible notebooks

### Deliverables

* GitHub release
* Research papers
* Public documentation

### Status

Future

---

# Long-Term Vision

Future extensions may include:

* Real-time biomechanical feedback
* Foundation models for human movement
* Wearable robotics integration
* Clinical movement assessment
* Multi-sport biomechanics platform
* Digital twin of athlete movement

---

# Progress Tracking

| Phase | Description               | Status         |
| ----- | ------------------------- | -------------- |
| 0     | Project Foundation        | ✅ Completed    |
| 1     | Literature Review         | 🔄 In Progress |
| 2     | Experimental Design       | ⏳ Planned      |
| 3     | Data Acquisition          | ⏳ Planned      |
| 4     | Data Processing           | ⏳ Planned      |
| 5     | Markerless Motion Capture | ⏳ Planned      |
| 6     | Sensor Fusion             | ⏳ Planned      |
| 7     | OpenSim Simulation        | ⏳ Planned      |
| 8     | Machine Learning          | ⏳ Planned      |
| 9     | Validation                | ⏳ Planned      |
| 10    | Scientific Dissemination  | 🚀 Future      |

---

# Guiding Principle

Every completed phase should produce reusable code, reproducible documentation, and scientific knowledge that contributes to the long-term development of TennisLabAI.
