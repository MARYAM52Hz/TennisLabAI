# Literature Review

## Overview

This document summarizes and analyzes the scientific literature relevant to the TennisLabAI project.

Rather than listing papers, the objective is to extract reusable scientific knowledge that informs the design, implementation, and evaluation of the framework.

Each reviewed publication should answer the following questions:

* What problem does the paper solve?
* What sensing modalities are used?
* What algorithms are proposed?
* How is the system evaluated?
* What limitations remain?
* How can the findings contribute to TennisLabAI?

---

# Research Themes

The literature is organized according to major research themes.

## Theme 1 — Tennis Biomechanics

Focus:

* Tennis serve biomechanics
* Forehand biomechanics
* Backhand biomechanics
* Injury mechanisms
* Performance analysis

Relevant Questions

* Which biomechanical variables are commonly studied?
* Which joints are most important?
* What evaluation metrics are used?

---

## Theme 2 — Wearable IMU Systems

Focus

* IMU-based motion analysis
* Wearable biomechanics
* Noraxon systems
* Inertial sensing

Relevant Questions

* Sensor placement
* Sampling frequency
* Calibration
* Drift compensation
* Feature extraction

---

## Theme 3 — Markerless Motion Capture

Focus

* MediaPipe
* RTMPose
* OpenPose
* OpenCap
* Vision Transformers

Relevant Questions

* Pose estimation accuracy
* Occlusion handling
* Sports applications
* 3D reconstruction

---

## Theme 4 — Sensor Fusion

Focus

* IMU + Camera Fusion
* Kalman filtering
* Deep sensor fusion
* Multimodal learning

Relevant Questions

* Which fusion strategies are most effective?
* What improvements are reported?

---

## Theme 5 — OpenSim and Musculoskeletal Simulation

Focus

* Inverse kinematics
* Inverse dynamics
* Muscle force estimation
* Joint loading

Relevant Questions

* Which variables can only be estimated through simulation?
* How is OpenSim validated?

---

## Theme 6 — Artificial Intelligence for Sports

Focus

* Performance prediction
* Skill assessment
* Injury prediction
* Movement classification

Relevant Questions

* Which models are commonly used?
* Which features are most informative?

---

# Paper Review Template

Each paper should be documented using the following structure.

## Citation

Authors

Year

Title

Journal / Conference

DOI

---

## Research Objective

What problem does the paper address?

---

## Participants

Number of participants

Population

Sport

---

## Sensors

Examples:

* IMU
* RGB Camera
* Motion Capture
* EMG
* Force Plate

---

## Experimental Tasks

Examples:

* Tennis serve
* Walking
* Running
* Jumping

---

## Algorithms

Examples:

* MediaPipe
* OpenPose
* Kalman Filter
* LSTM

---

## Outputs

Examples:

* Joint angles
* Muscle forces
* Movement classification

---

## Evaluation Metrics

Examples:

* RMSE
* ICC
* Correlation
* Bland–Altman

---

## Main Findings

Summarize the key scientific contributions.

---

## Limitations

List the main limitations identified by the authors.

---

## Ideas for TennisLabAI

Describe how this paper influences or improves the TennisLabAI framework.

---

# Reading Progress

Maintain a running summary of reviewed literature.

Example

| Theme                     | Papers Reviewed | Status      |
| ------------------------- | --------------: | ----------- |
| Tennis Biomechanics       |               0 | Not Started |
| IMU Systems               |               0 | Not Started |
| Markerless Motion Capture |               0 | Not Started |
| Sensor Fusion             |               0 | Not Started |
| OpenSim                   |               0 | Not Started |
| AI for Sports             |               0 | Not Started |

Update this table throughout the project.
