🎾 TennisLabAI

A Multimodal AI Framework for Markerless Tennis Biomechanics

Bridging Computer Vision, Wearable IMUs, Musculoskeletal Simulation, and Artificial Intelligence for Explainable Sports Biomechanics.

Overview

TennisLabAI is an open scientific research framework for multimodal human motion analysis in tennis.

The project integrates:

Markerless Motion Capture
Wearable IMU Sensors
Musculoskeletal Simulation (OpenSim)
Machine Learning
Sensor Fusion
Explainable AI

to build a reproducible pipeline for biomechanics research beyond traditional motion capture laboratories.

Unlike conventional biomechanics workflows that rely exclusively on laboratory equipment, TennisLabAI investigates how low-cost RGB cameras can be combined with wearable sensors to achieve reliable biomechanical measurements in real-world environments.

Research Vision

The long-term vision of TennisLabAI is to establish an open scientific ecosystem for multimodal sports biomechanics.

The framework aims to bridge laboratory-grade sensing with modern computer vision, enabling accurate, reproducible, and explainable movement analysis for:

Researchers
Sports Scientists
Coaches
Clinicians
Athletes

Although tennis serves as the primary case study, the framework is designed to generalize to other sports and human movement analysis applications.

Research Questions

This project investigates several key scientific questions.

Can markerless computer vision estimate biomechanical variables with accuracy comparable to laboratory-grade IMU systems?
How can multimodal sensor fusion improve robustness and reliability?
Which biomechanical variables are most informative for performance assessment and injury prevention?
Can musculoskeletal simulation improve the interpretability of computer vision measurements?
How can explainable AI support personalized coaching?
Research Ecosystem

TennisLabAI is part of a larger research ecosystem.

                     TennisLabAI Ecosystem

                 ┌────────────────────────────┐
                 │      TennisLabAI           │
                 │  AI + Biomechanics Engine  │
                 └──────────────┬─────────────┘
                                │
                                │ consumes
                                ▼
      ┌────────────────────────────────────────────┐
      │ TennisLabAI Annotation Protocol            │
      │ Human-in-the-Loop Gold Standard Annotation │
      └────────────────────────────────────────────┘
                                │
                                │ generates
                                ▼
              Gold Standard Biomechanics Dataset
Pipeline
Athlete

│

├── RGB Camera

├── Wearable IMU

│

▼

Synchronization

▼

Pose Estimation

▼

Sensor Fusion

▼

OpenSim

▼

Machine Learning

▼

Performance Assessment

▼

Injury Risk Prediction
Repository Structure
src/
├── pose_estimation/
├── imu/
├── opensim/
├── fusion/
├── ml/
├── evaluation/
└── visualization/
Related Repository
TennisLabAI Annotation Protocol

The annotation methodology used in this project is documented separately.

It defines:

Annotation Taxonomy
CVAT Skeleton Specification
Human-in-the-Loop Workflow
IMU Validation
Gold Standard Dataset Schema

The resulting annotations are consumed by TennisLabAI for training, evaluation, and biomechanical analysis.

Current Status

Current development focuses on:

Repository architecture
Experimental design
Annotation framework integration
Dataset protocol development
Sensor synchronization
OpenSim integration

Implementation is being added incrementally.

Long-Term Goal

Develop an open scientific platform for multimodal biomechanics that supports reproducible research and can be extended beyond tennis to general human movement analysis.


Serve Reel Module (serve_reel/)

A working, tested one-command pipeline that turns a single phone video of a tennis serve plus CVAT labels into an analysis reel (3D reconstruction, joint-angle scorecard against the literature, posture charts, serve-type check) with an explicit reliability grade (A-D) for every reported number.

Highlights

Two camera setups: behind the baseline (scale from court points) and at the side (scale from player height)
Single-camera 3D lift with constant bone lengths, ballistic ball fit (gravity as an independent scale check)
Optional posture charts (--charts) and a reliability/QC system (qc.json, qc.md)
Specification of video standards, label properties, scale calibration with and without labels, and handling of human labelling error

Start here: serve_reel/README.md. Standards and calibration: docs/serve_reel/INPUT_STANDARDS_AND_CALIBRATION.md. Pipeline, data formats, decisions, extension recipes: docs/serve_reel/.
