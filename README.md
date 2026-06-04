# AI & Machine Learning — From Zero to Neural Networks

A hands-on, exercise-driven learning path. Each module builds on the previous one.
Work through the notebooks in order — every concept is introduced with examples,
then you practice with exercises marked with `# TODO`.

## Prerequisites

- Python 3.10+
- Basic programming knowledge (variables, loops, functions)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

## Run in Zed (REPL)

Every notebook has a paired `.py` twin (same name, percent format) for [Zed's REPL](https://zed.dev/docs/repl):

1. Open the module's `.py` file in Zed (e.g. `01_python_foundations/01_numpy_basics.py`)
2. Put the cursor in a `# %%` cell, press `ctrl-shift-enter` to run it — output & plots render inline
3. The `.py` and `.ipynb` stay paired; sync edits with `jupytext --sync <file>`

> The `.ipynb` files keep saved outputs; the `.py` twins do not (output is live-only in Zed).

## Learning Path

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 01 | [Python Foundations](01_python_foundations/) | NumPy, Pandas, Matplotlib — the ML toolkit |
| 02 | [Math Foundations](02_math_foundations/) | Linear algebra & statistics you actually need |
| 03 | [First ML Models](03_first_ml_models/) | Linear & logistic regression from scratch and with scikit-learn |
| 04 | [Classification & Trees](04_classification_and_trees/) | Decision trees, model evaluation, confusion matrices |
| 05 | [Unsupervised Learning](05_unsupervised_learning/) | K-Means clustering, PCA, dimensionality reduction |
| 06 | [Ensemble Methods](06_ensemble_methods/) | Random Forest, Gradient Boosting, XGBoost |
| 07 | [Neural Networks](07_neural_networks/) | Build your first neural net with PyTorch |
| 08 | [CNNs & Images](08_cnns_image_classification/) | Convolutional neural networks, image classification |
| 09 | [NLP & Text](09_nlp_text_processing/) | Text processing, embeddings, intro to transformers |
| 10 | [Capstone Project](10_capstone_project/) | End-to-end ML project pulling it all together |

### Advanced Image AI track (generative vision)

An optional deep-dive that builds, step by step, toward a **working hairstyle swap** —
take person A's face and give them person B's hair. Each module first builds the idea
*from scratch* to understand it, then uses pretrained SOTA models.

| # | Module | What You'll Learn |
|---|--------|-------------------|
| 11 | [Segmentation & Face Parsing](11_segmentation_face_parsing/) | U-Net from scratch, pixel-wise labels, hair masks |
| 12 | [Autoencoders & VAEs](12_autoencoders_vae/) | Latent spaces, the reparameterization trick, interpolation |
| 13 | [GANs from Scratch](13_gans/) | DCGAN, adversarial training, the road to StyleGAN |
| 14 | [StyleGAN & GAN Inversion](14_stylegan_inversion/) | Style mixing, inverting real photos, latent hair blend *(GPU)* |
| 15 | [Diffusion Models](15_diffusion/) | DDPM from scratch, Stable Diffusion inpainting *(GPU)* |
| 16 | [Capstone — Hairstyle Swap](16_capstone_hairstyle_swap/) | Align → mask → generate → blend, end to end |

> **Hardware:** Modules 11–13 and the local sections of 14–16 run on a Mac (CPU/MPS).
> The heavy models (StyleGAN2, Stable Diffusion) need a GPU — run those sections on
> **Google Colab** (Runtime → GPU). Every notebook is guarded so it runs top-to-bottom
> either way; GPU-only cells skip with notes when no GPU is present.

## How to Use

1. Open the notebook for each module in Jupyter
2. Read through the explanations and run the example cells
3. Complete the `# TODO` exercises — solutions are in separate cells you can reveal
4. Move to the next module when you're comfortable

## Tips

- **Don't skip the exercises** — reading is not learning, doing is
- **Experiment** — change parameters, break things, see what happens
- **Re-run from scratch** — use "Restart & Run All" to make sure your code works end-to-end
