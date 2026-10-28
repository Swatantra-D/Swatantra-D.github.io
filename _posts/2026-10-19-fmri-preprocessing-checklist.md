---
title: "A practical checklist for fMRI preprocessing"
date: 2026-10-19
tags: [fMRI, methods, checklist]
draft_badge: true
excerpt: "From raw scans to clean regional time series: the steps, decisions and quality checks I keep coming back to, with a short Nilearn example."
---

Preprocessing is where most fMRI analyses quietly succeed or fail. Here is the checklist I keep coming back to when I take raw scans to clean regional time series. It is opinionated and incomplete, but it catches the common mistakes.

<!--more-->

## Before you touch the data

- **Organise the dataset in BIDS** and run the BIDS validator. Most modern tools assume it.
- **Write down the acquisition details**: repetition time (TR), slice timing, phase-encoding direction, and whether field maps exist.
- **Look at the raw images.** Run MRIQC or simply scroll through a few runs. Artefacts are easier to catch before they are smoothed away.
{: .checklist}

## Core preprocessing

fMRIPrep handles most of this robustly and writes an HTML report for every subject. Read the reports.

- Head-motion estimation and correction.
- Slice-timing correction, if appropriate for your TR and analysis.
- Susceptibility distortion correction, using field maps when you have them.
- Co-registration of functional data to the subject's anatomical image.
- Spatial normalisation to a standard template, if you compare across subjects.
- Confound estimation: motion parameters, framewise displacement (FD), DVARS, white-matter and CSF signals, CompCor components.
{: .checklist}

## Denoising: decide, don't default

- **Choose a confound strategy before looking at results**: for example, motion parameters and their derivatives, WM/CSF signals, and optionally the global signal (still debated).
- **Censor high-motion volumes** (“scrubbing”) using an FD threshold that you set and report in advance.
- **Filter and regress together.** Apply temporal filtering in the same step as nuisance regression, so the regression does not reintroduce frequencies you removed.
{: .checklist}

## Extract regional time series

With an atlas and the fMRIPrep confounds, Nilearn makes this short:

```python
from nilearn import datasets
from nilearn.interfaces.fmriprep import load_confounds_strategy
from nilearn.maskers import NiftiLabelsMasker

atlas = datasets.fetch_atlas_schaefer_2018(n_rois=200)
confounds, sample_mask = load_confounds_strategy(
    bold_file, denoise_strategy="scrubbing", fd_threshold=0.5
)
masker = NiftiLabelsMasker(
    labels_img=atlas.maps,
    standardize="zscore_sample",
    detrend=True,
    high_pass=0.01,
    low_pass=0.08,
    t_r=2.0,  # use your own TR
)
time_series = masker.fit_transform(
    bold_file, confounds=confounds, sample_mask=sample_mask
)
```

## Quality control you shouldn't skip

- **Carpet plots** before and after denoising.
- **FD and DVARS distributions** per subject, with exclusion criteria fixed in advance.
- **Registration**, checked by eye for a sample of subjects.
- **Motion against your variable of interest.** In ageing studies, older participants often move more, so motion can masquerade as an age effect. Check, and model it.
- **How many volumes survive scrubbing** in each group.
{: .checklist}

## Make it reproducible

- Pin software versions; run fMRIPrep from a container and record the version.
- Keep the exact command lines and configuration files under version control.
- On a cluster, use Slurm job arrays so that every subject is processed identically.
- Log every exclusion and the reason for it.
{: .checklist}

None of this is glamorous, but each item is a decision a reviewer may ask about. Having the answers written down, ideally in code, is what makes the later analyses trustworthy.
