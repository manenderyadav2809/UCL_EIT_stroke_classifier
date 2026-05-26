"""
clinical_interpretations.py
---------------------------
Per-scan lesion annotations for all 19 patients with PDF reports.

Each patient may have:
  - report_A: usually the initial / acute CT
  - report_B: usually a follow-up CT or MRI

Where both exist, both are annotated separately. Where only one exists,
report_B is omitted.

Each scan annotation contains:
  scan_label:     "Report A" / "Report B"
  modality:       free text from the report (e.g. "CT" / "MRI" / "CT + CTA")
  timing:         free text describing when (e.g. "initial acute" / "24h follow-up")
  date:           date string from the report
  side:           "left" / "right" / "bilateral" / "midline" / "none"
                  ("none" means no acute lesion identified on this scan)
  regions:        list of region keys from head_anatomy.py
                  e.g. ["frontal_left", "temporal_left", "insula_left"]
                  Empty list = no localizable lesion (deep or null scan).
  source_phrase:  verbatim phrase(s) from this scan's section of the report
  notes:          analyst comments (size, depth, certainty, etc.)
"""

PATIENT_SCANS = {

    # =========================================================================
    "Patient_01": {
        "summary": "Left MCA cortical infarct, subacute.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial, outside thrombolysis window",
            "date": "04/05/2016",
            "side": "left",
            "regions": ["frontal_left", "insula_left"],
            "source_phrase": (
                "diminished grey-white matter differentiation involving the "
                "left precentral gyrus, in keeping with a subacute infarct "
                "within the territory of the left middle cerebral artery "
                "with further low attenuation suspicious for infarction "
                "demonstrated in the left insula"
            ),
            "notes": (
                "Precentral gyrus → frontal-central border (I'm placing in "
                "frontal_left as the closest single region). Insula explicit."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI + MRA",
            "timing": "Next-day follow-up",
            "date": "05/05/2016",
            "side": "left",
            "regions": ["frontal_left", "parietal_left", "insula_left"],
            "source_phrase": (
                "diffusion restriction involving the left precentral gyrus "
                "and superior frontal gyrus ... acute MCA territory infarct. "
                "Further recent infarcts are shown in the left parietal "
                "lobe and involving the dorsal aspect of the left insula"
            ),
            "notes": (
                "MRI confirms and extends: frontal (precentral + sup. frontal) "
                "+ parietal + insula. All left."
            ),
        },
    },

    # =========================================================================
    "Patient_03": {
        "summary": "Left paracentral lobule haematoma, possible underlying lesion.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT",
            "timing": "Initial acute",
            "date": "10/05/2016",
            "side": "left",
            "regions": ["paracentral_left"],
            "source_phrase": (
                "acute intraparenchymal haematoma centred onto the left "
                "paracentral lobule"
            ),
            "notes": (
                "Paracentral lobule = medial central, near midline. "
                "Used the paracentral_left specific region."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI + MRA + contrast",
            "timing": "Follow-up, evaluating for underlying mass",
            "date": "11/05/2016",
            "side": "left",
            "regions": ["paracentral_left"],
            "source_phrase": (
                "evolving haematoma centred on the left paracentral lobule "
                "is again shown. Within its centre, there is a conspicuous "
                "rounded focus of T1/FLAIR hyperintensity and more marked "
                "susceptibility effect ... suspicious for an underlying "
                "lesion containing older blood products"
            ),
            "notes": (
                "Same location; MRI raises concern for underlying tumour / "
                "cavernoma. Lesion site is unchanged."
            ),
        },
    },

    # =========================================================================
    "Patient_04": {
        "summary": "Large right MCA infarct, basal ganglia + insula + cortex.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT",
            "timing": "24h post-thrombolysis follow-up",
            "date": "12/05/2016",
            "side": "right",
            "regions": [
                "insula_right", "basal_ganglia_right",
                "temporal_right", "frontal_right",
            ],
            "source_phrase": (
                "large right sided MCA infarct ... hypoattenuation involving "
                "the insula, basal ganglia and Cortex at the ganglionic "
                "level with associated Sulcal effacement ... right M1/M2 MCA"
            ),
            "notes": (
                "Follow-up CT shows extent. Mixed cortical + deep (basal "
                "ganglia). 'Cortex at ganglionic level' is hard to assign "
                "to one lobe — I included frontal and temporal which are "
                "the cortical regions at that level."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT + CTA",
            "timing": "Initial pre-thrombolysis",
            "date": "11/05/2016",
            "side": "right",
            "regions": [
                "basal_ganglia_right", "insula_right",
                "temporal_right", "frontal_right",
            ],
            "source_phrase": (
                "right basal ganglia territory and right insula. Subtle "
                "sulcal effacement also noted in the right temporal lobe "
                "and frontal temporal opercular regions ... occluded right "
                "internal carotid artery"
            ),
            "notes": (
                "Initial pre-thrombolysis CT. Reports A and B describe the "
                "same lesion at different timepoints (B is earlier despite "
                "being labelled 'B' in the PDF)."
            ),
        },
    },

    # =========================================================================
    "Patient_05": {
        "summary": "Small acute left thalamic haematoma + posterior internal capsule.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "MRI + MRA",
            "timing": "Follow-up after CT",
            "date": "20/05/2016",
            "side": "left",
            "regions": ["thalamus_left"],
            "source_phrase": (
                "parenchymal haematoma centred on the left thalamus is "
                "again shown, with a small amount of surrounding oedema"
            ),
            "notes": "Pure deep lesion. No cortical involvement.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT + CTA",
            "timing": "Initial acute",
            "date": "20/05/2016",
            "side": "left",
            "regions": ["thalamus_left", "internal_capsule_left"],
            "source_phrase": (
                "small acute intraparenchymal haematoma centred on the "
                "lateral aspect of the left thalamus and adjacent posterior "
                "limb of the left internal capsule"
            ),
            "notes": "Pure deep. Thalamus + posterior internal capsule.",
        },
    },

    # =========================================================================
    "Patient_06": {
        "summary": "Right occipital lobar haemorrhage.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Follow-up of external CT",
            "date": "24/05/2016",
            "side": "right",
            "regions": ["occipital_right"],
            "source_phrase": (
                "focus of high density is evident within the right occipital "
                "lobe measuring approximately 2.3cm x 1.5cm and is in "
                "keeping with an acute parenchymal haematoma"
            ),
            "notes": "Pure cortical occipital. ~2.3cm — small-to-medium.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Same-day MRI follow-up",
            "date": "24/05/2016",
            "side": "right",
            "regions": ["occipital_right"],
            "source_phrase": (
                "right occipital lobar haemorrhage with mild surrounding "
                "mass effect"
            ),
            "notes": "Confirms occipital location.",
        },
    },

    # =========================================================================
    "Patient_07": {
        "summary": "Right MCA perforator (lacunar) infarcts — lentiform + caudate.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial acute",
            "date": "24/05/2016",
            "side": "none",
            "regions": [],
            "source_phrase": (
                "No evidence of an acute cortical or large vessel "
                "territorial infarct. No significant findings demonstrated "
                "on CTA."
            ),
            "notes": "Initial CT was negative. No localizable lesion at this scan.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Follow-up after symptoms worsened",
            "date": "unknown (later)",
            "side": "right",
            "regions": ["basal_ganglia_right"],
            "source_phrase": (
                "diffusion restriction with ADC depression centred upon the "
                "right lentiform nucleus ... additional focus of diffusion "
                "restriction centred upon the right caudate head"
            ),
            "notes": (
                "Lentiform + caudate are both in basal ganglia. Lacunar / "
                "perforator territory — pure deep lesion."
            ),
        },
    },

    # =========================================================================
    "Patient_09": {
        "summary": "Right MCA cortical infarct — temporal + insula + supramarginal.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT",
            "timing": "Initial acute",
            "date": "25/05/2016",
            "side": "right",
            "regions": ["temporal_right", "insula_right"],
            "source_phrase": (
                "loss of grey-white matter differentiation of the right "
                "anterior temporal lobe and Subjacent insular Cortex ... "
                "Acute right MCA territory infarct"
            ),
            "notes": "Anterior temporal + insula. Right MCA.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Next-day follow-up",
            "date": "26/05/2016",
            "side": "right",
            "regions": ["temporal_right", "insula_right", "parietal_right"],
            "source_phrase": (
                "mild diffusion restriction located in the right superior "
                "and middle temporal gyrus extending to the insular cortex, "
                "right supramarginal gyrus and subjacent corona radiata"
            ),
            "notes": (
                "MRI adds supramarginal gyrus = inferior parietal. So: "
                "temporal + insula + parietal. Right MCA."
            ),
        },
    },

    # =========================================================================
    "Patient_10": {
        "summary": "Left MCA cortical infarcts — parietal + temporal.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT",
            "timing": "Initial",
            "date": "30/05/2016",
            "side": "none",
            "regions": [],
            "source_phrase": "No sign of intracranial bleeding.",
            "notes": (
                "Initial CT negative. Scalp haematoma over left "
                "parieto-occipital noted but that's external (subcutaneous), "
                "not a brain lesion."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI + MRA + Carotids",
            "timing": "Next-day follow-up",
            "date": "31/05/2016",
            "side": "left",
            "regions": ["parietal_left", "temporal_left"],
            "source_phrase": (
                "patchy areas of diffusion restriction in keeping with "
                "acute MCA territory infarcts involving the left inferior "
                "parietal and temporal lobe"
            ),
            "notes": "MRI reveals the lesion. Left inferior parietal + temporal.",
        },
    },

    # =========================================================================
    "Patient_11": {
        "summary": "Large right frontal haematoma with mass effect, multiple bilateral bleeds.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT",
            "timing": "Acute, after seizures",
            "date": "07/06/2016",
            "side": "right",   # dominant lesion on right; bilateral involvement
            "regions": [
                "frontal_right", "central_right",
                "basal_ganglia_right",  # right striatocapsular mass effect
                "frontal_left", "temporal_left",  # smaller left-sided foci
            ],
            "source_phrase": (
                "massive acute intraparenchymal haematoma involving most of "
                "the right frontal lobe, the right operculum and the right "
                "postcentral gurus ... small focal haematoma also shown "
                "involving the left middle temporal gyrus ... mass effect "
                "on underlying brain parenchyma including the right "
                "striatocapsular region ... left inferior frontal and left "
                "postcentral region"
            ),
            "notes": (
                "Dominant bleed: right frontal + opercular + postcentral. "
                "Smaller bleed: left middle temporal. Mass effect on right "
                "striatocapsular. Treating as right-dominant with bilateral "
                "involvement. Postcentral gyrus = central."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Earlier reference scan (10/02/2016)",
            "date": "10/02/2016",
            "side": "bilateral",
            "regions": ["central_left", "frontal_right", "frontal_left"],
            "source_phrase": (
                "acute parenchymal haemorrhages centred on the subcortical "
                "white matter of the left postcentral gyrus, right middle "
                "frontal gyrus, and left orbitofrontal region"
            ),
            "notes": (
                "Different episode — months earlier. Bilateral haemorrhages. "
                "Provides context but this is not the acute scan that "
                "drove the EIT recording timing."
            ),
        },
    },

    # =========================================================================
    "Patient_12": {
        "summary": "Left medial occipital PCA infarct (evolved from initially-negative CT).",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial acute",
            "date": "08/06/2016",
            "side": "none",
            "regions": [],
            "source_phrase": (
                "No acute infarct. Established right lenticulostriate and "
                "left hemipontine infarct."
            ),
            "notes": (
                "Initial CT showed no acute infarct, only chronic / "
                "established. Chronic lesions ignored."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT",
            "timing": "24h post-thrombolysis",
            "date": "09/06/2016",
            "side": "left",
            "regions": ["occipital_left"],
            "source_phrase": (
                "small area of low density in the left medial occipital "
                "lobe, in keeping with an evolving left PCA territory "
                "infarct"
            ),
            "notes": "Left medial occipital, PCA territory. Cortical.",
        },
    },

    # =========================================================================
    "Patient_14": {
        "summary": "Left insular / opercular infarct (MCA branch with calcific embolus).",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial, pre-thrombolysis",
            "date": "11/06/2016",
            "side": "left",
            "regions": ["insula_left"],
            "source_phrase": (
                "Possible acute infarct in the left insular lobe ... "
                "calcification projected over the left insular branch MCA "
                "with reduced flow seen distally"
            ),
            "notes": (
                "Possible acute insular infarct. Mature infarct in frontal "
                "operculum noted as chronic — not counted."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT",
            "timing": "Post-thrombolysis",
            "date": "12/06/2016",
            "side": "left",
            "regions": ["insula_left", "frontal_left", "temporal_left"],
            "source_phrase": (
                "infarct centred upon the left insular cortex, left frontal "
                "and temporal opercula"
            ),
            "notes": "Insula + frontal + temporal opercula. Left MCA branch.",
        },
    },

    # =========================================================================
    "Patient_15": {
        "summary": "Left MCA infarct — parietal + insula (initially called parieto-occipital).",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial",
            "date": "20/06/2016",
            "side": "left",
            "regions": ["parietal_left", "occipital_left"],
            "source_phrase": (
                "Left parieto-occipital lobe subacute infarct with "
                "localised mass effect"
            ),
            "notes": "CT called it parieto-occipital. MRI later refined.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Two-day follow-up",
            "date": "22/06/2016",
            "side": "left",
            "regions": ["parietal_left", "insula_left"],
            "source_phrase": (
                "diffusion restriction with corresponding low ADC values "
                "located in the left inferior 1 superior parietal lobule, "
                "parietal operculum and dorsal aspect of the left insular "
                "cortex ... Acute/subacute left MCA territory infarct"
            ),
            "notes": (
                "MRI refines to parietal + insula. MCA territory, not PCA — "
                "supersedes the initial parieto-occipital read."
            ),
        },
    },

    # =========================================================================
    "Patient_16": {
        "summary": "Bilateral embolic infarcts — right peri-Rolandic + left posterior frontal.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial",
            "date": "26/06/2016",
            "side": "none",
            "regions": [],
            "source_phrase": "No acute intracranial infarct demonstrated.",
            "notes": "Initial CT negative (too early to visualize).",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI + MRA",
            "timing": "Next-day follow-up",
            "date": "27/06/2016",
            "side": "bilateral",
            "regions": ["central_right", "frontal_left"],
            "source_phrase": (
                "restricted diffusion seen in the right peri-Rolandic "
                "region (pre and post central gyrus) and a focus of "
                "restricted diffusion is seen in the posterior left "
                "frontal lobe ... two different territories suggest a "
                "central thromboembolic source"
            ),
            "notes": (
                "Bilateral embolic — right central (peri-Rolandic) AND "
                "left posterior frontal. Two separate areas."
            ),
        },
    },

    # =========================================================================
    "Patient_17": {
        "summary": "Right striatocapsular / thalamic haematoma — pure deep.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "MRI + MRA",
            "timing": "4-day follow-up",
            "date": "04/07/2016",
            "side": "right",
            "regions": [
                "thalamus_right", "basal_ganglia_right",
                "internal_capsule_right",
            ],
            "source_phrase": (
                "Right striato-capsular / thalamic microhaemorrhage ... "
                "localised mass effect effacing the right lateral "
                "ventricle, third ventricle and lateral aspect of the "
                "right midbrain"
            ),
            "notes": (
                "Pure deep. Thalamus + basal ganglia + internal capsule "
                "all involved (striatocapsular)."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT + CTA",
            "timing": "Initial acute",
            "date": "30/06/2016",
            "side": "right",
            "regions": [
                "thalamus_right", "basal_ganglia_right",
                "internal_capsule_right",
            ],
            "source_phrase": (
                "acute intraparenchymal haematoma involving the right "
                "thalamus and striato-capsular region measuring approximately "
                "2.5 cm x 1.9 cm"
            ),
            "notes": "Same lesion, initial scan. 2.5 cm bleed.",
        },
    },

    # =========================================================================
    "Patient_18": {
        "summary": "Left premotor cortex infarct (acute), mature lentiform lacune (chronic).",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial",
            "date": "02/07/2016",
            "side": "left",
            "regions": ["internal_capsule_left", "basal_ganglia_left"],
            "source_phrase": (
                "Possible infarct involving the left internal capsule / "
                "lentiform nucleus"
            ),
            "notes": (
                "CT suggested deep lesion. MRI later showed acute lesion "
                "is actually cortical (premotor). The deep finding is a "
                "mature lacune, not acute."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI",
            "timing": "Two-day follow-up",
            "date": "04/07/2016",
            "side": "left",
            "regions": ["premotor_left"],
            "source_phrase": (
                "diffusion restriction demonstrated in the left premotor "
                "cortex consistent with an acute left MCA infarct ... "
                "Mature lacunar infarct in the left lentiform nucleus"
            ),
            "notes": (
                "ACUTE lesion = left premotor cortex (frontal). The "
                "lentiform lacune is MATURE (chronic) — ignored. The MRI "
                "supersedes the CT for lesion identification."
            ),
        },
    },

    # =========================================================================
    "Patient_19": {
        "summary": "Large right MCA infarct — frontal + temporal + parietal + insula + basal ganglia.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial, pre-thrombolysis",
            "date": "05/07/2016",
            "side": "right",
            "regions": [
                "insula_right", "frontal_right",
                "temporal_right", "parietal_right",
                "basal_ganglia_right",
            ],
            "source_phrase": (
                "loss of the grey-white matter differentiation and sulcal "
                "effacement involving the right insula, frontoparietal and "
                "temporal operculum, and the right lentiform nucleus is "
                "indistinct in keeping with acute infarction in the right "
                "MCA territory"
            ),
            "notes": (
                "Right ICA tip thrombus → big right MCA infarct. Insula + "
                "fronto-parietal + temporal opercula + lentiform = wide."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT",
            "timing": "24h post-thrombolysis",
            "date": "05/07/2016 (later)",
            "side": "right",
            "regions": [
                "frontal_right", "temporal_right", "parietal_right",
                "insula_right", "basal_ganglia_right",
            ],
            "source_phrase": (
                "conspicuous low attenuation involving the right frontal, "
                "temporal and parietal lobes, insula and basal ganglia, in "
                "keeping with an evolving acute right MCA territory infarct"
            ),
            "notes": "Same lesion, evolved. All of right MCA territory.",
        },
    },

    # =========================================================================
    "Patient_20": {
        "summary": "Acute left occipital haematoma (probable amyloid angiopathy).",
        "report_A": {
            "scan_label": "Report A",
            "modality": "MRI + MRA",
            "timing": "Day-after-external-CT MRI",
            "date": "06/07/2016",
            "side": "left",
            "regions": ["occipital_left"],
            "source_phrase": (
                "T1 shortening, restricted diffusion and susceptibility in "
                "the left occipital lobe, corresponding to the acute "
                "haematoma demonstrated on the CT study ... Acute left "
                "occipital hematoma"
            ),
            "notes": (
                "Pure cortical occipital lobar bleed. Microhaemorrhages "
                "elsewhere are chronic (amyloid) — not counted."
            ),
        },
        # No Report B available
    },

    # =========================================================================
    "Patient_21": {
        "summary": "Right MCA temporoparietal infarct + smaller left occipital infarct.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "CT + CTA",
            "timing": "Initial",
            "date": "13/07/2016",
            "side": "right",
            "regions": ["temporal_right", "parietal_right"],
            "source_phrase": (
                "right temporoparietal wedge-shaped area of low attenuation "
                "in keeping with subacute infarct"
            ),
            "notes": "Right temporoparietal. MCA territory.",
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "MRI + MRA",
            "timing": "Next-day follow-up",
            "date": "14/07/2016",
            "side": "bilateral",
            "regions": [
                "parietal_right", "temporal_right", "insula_right",
                "occipital_left",
            ],
            "source_phrase": (
                "acute right parietotemporal and insular infarct is "
                "confirmed on MRI. Further small acute cortical infarcts "
                "are seen in the left inferior occipital lobe"
            ),
            "notes": (
                "MRI shows both: dominant right parietotemporal+insula, "
                "smaller left occipital. Bilateral. Old right thalamic "
                "lacune ignored (chronic)."
            ),
        },
    },

    # =========================================================================
    "Patient_23": {
        "summary": "Large right frontal haematoma with multiple chronic microbleeds.",
        "report_A": {
            "scan_label": "Report A",
            "modality": "MRI + MRA",
            "timing": "Follow-up to external CT",
            "date": "22/07/2016",
            "side": "right",
            "regions": ["frontal_right"],
            "source_phrase": (
                "large right frontal intraparenchymal haemorrhage"
            ),
            "notes": (
                "Pure cortical right frontal. Multiple microbleeds and "
                "scattered chronic bleeds throughout — not counted (chronic "
                "background, likely cavernomata)."
            ),
        },
        "report_B": {
            "scan_label": "Report B",
            "modality": "CT Angio",
            "timing": "Day prior, looking for vascular cause",
            "date": "21/07/2016",
            "side": "right",
            "regions": ["frontal_right"],
            "source_phrase": (
                "intraparenchymal right frontal haematoma is again noted"
            ),
            "notes": "Same lesion, day earlier.",
        },
    },
}
