# Experimental Protocol

## Overview

This document defines the experimental protocol for the TennisLabAI project.

The objective is to establish a standardized and reproducible methodology for collecting synchronized multimodal biomechanical data during tennis movements.

The protocol is designed to ensure consistency across experiments while allowing future extensions and additional sensing modalities.

---

# 1. Experimental Objectives

The experiments aim to:

* Collect synchronized IMU and RGB video data.
* Compare wearable inertial sensing with markerless computer vision.
* Generate biomechanical variables for scientific analysis.
* Evaluate the agreement between sensing modalities.
* Build datasets for machine learning applications.

---

# 2. Participants

The following information should be recorded for each participant.

## Participant Information

* Anonymous Participant ID
* Age
* Sex (if required by the study)
* Height
* Weight
* Dominant hand
* Tennis playing experience
* Competition level

---

# 3. Equipment

## Wearable Sensors

Noraxon Ultium myoMOTION IMU system

Potential measurements include:

* Segment orientation
* Linear acceleration
* Angular velocity

---

## Camera System

RGB cameras

Optional:

* High-speed cameras
* Multi-camera setup

---

## Software

* Pose estimation framework
* OpenSim
* Data synchronization tools
* Machine learning pipeline

---

# 4. Experimental Environment

Record:

* Laboratory location
* Court type
* Lighting conditions
* Camera placement
* Sensor placement

---

# 5. Tennis Tasks

Each participant performs multiple repetitions of standardized tennis movements.

Potential tasks include:

* Flat serve
* Slice serve
* Kick serve
* Forehand drive
* Backhand drive
* Volley
* Ready position

Additional tasks may be added depending on the study.

---

# 6. Sensor Placement

Document:

* Number of IMUs
* Body segments instrumented
* Sensor orientation
* Calibration procedure

A detailed placement diagram will be added in future revisions.

---

# 7. Data Acquisition

Record the following for every trial:

* Trial ID
* Date
* Participant ID
* Tennis task
* Trial number
* Recording duration
* Sampling frequency
* Camera frame rate

---

# 8. Synchronization Strategy

The following synchronization methods may be considered:

* Hardware synchronization
* Timestamp synchronization
* Event-based synchronization

Possible synchronization events:

* Ball impact
* Ground contact
* Start of movement

---

# 9. Data Processing Pipeline

The general workflow is:

Experiment

↓

Raw Data Collection

↓

Calibration

↓

Synchronization

↓

Preprocessing

↓

Pose Estimation

↓

IMU Processing

↓

Sensor Fusion

↓

Biomechanical Analysis

↓

Machine Learning

↓

Statistical Evaluation

↓

Results

---

# 10. Biomechanical Variables

Potential variables include:

## Kinematics

* Joint angles
* Segment orientation
* Angular velocity
* Angular acceleration
* Range of motion

---

## Performance Variables

* Racket speed
* Ball speed
* Swing duration
* Movement timing

---

## OpenSim Variables

* Joint moments
* Joint reaction forces
* Muscle forces
* Muscle activation estimates

---

# 11. Validation Strategy

Measurements obtained from computer vision will be compared with wearable inertial sensing.

Potential evaluation metrics include:

* RMSE
* MAE
* Pearson correlation
* Intraclass Correlation Coefficient (ICC)
* Bland–Altman analysis

---

# 12. Data Management

Experimental data should be organized using the repository structure.

Raw data, processed data, metadata, and analysis results should be stored separately.

Participant identities should remain anonymous.

---

# 13. Expected Outcomes

The protocol is expected to produce:

* Reproducible multimodal datasets
* Standardized biomechanical measurements
* Benchmark datasets for algorithm evaluation
* Publication-quality experimental results

---

# Future Updates

This protocol will evolve as new equipment, datasets, and experimental procedures are incorporated into the project.
