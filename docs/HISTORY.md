# Ontogenesis — experimental history

This is a retrospective engineering and scientific record of generations 0001–0021. Each generation is a separate reproducible experiment, not a continuation from a checkpoint. Source code is normative. Recorded values are single-seed observations from successful CI runs; hypotheses and limitations are explicitly separated. Parameters are dimensionless and the time step is one. L denotes the periodic nearest-neighbor discrete Laplacian. Active chemical coverage is the fraction of cells above 0.1; structural coverage uses M > 0.2. All runs use seed 42. Artifact links require GitHub authentication and expire; workflow links remain the durable regeneration path.

## Contents

- [0020 — Topological complexity](#generation-0020--topological-complexity)

- [0019 — Compartmentalization](#generation-0019--compartmentalization)

- [0018 — Morphogenesis](#generation-0018--morphogenesis)

- [0001 — Differentiation](#generation-0001--differentiation)
- [0002 — Diversification](#generation-0002--diversification)
- [0003 — Symmetry breaking](#generation-0003--symmetry-breaking)
- [0004 — Dynamics](#generation-0004--dynamics)
- [0005 — Feedback](#generation-0005--feedback)
- [0006 — Volumetric emergence](#generation-0006--volumetric-emergence)
- [0007 — Circulation](#generation-0007--circulation)
- [0008 — Energetics](#generation-0008--energetics)
- [0009 — Organization](#generation-0009--organization)
- [0010 — Communication](#generation-0010--communication)
- [0011 — Adaptation](#generation-0011--adaptation)
- [0012 — Hypervolume](#generation-0012--hypervolume)
- [0013 — Entities](#generation-0013--entities)
- [0014 — Observatory](#generation-0014--observatory)
- [0015 — Evolution](#generation-0015--evolution)
- [0016 — Genetics](#generation-0016--genetics)
- [0017 — Ecosystem](#generation-0017--ecosystem)

## Generation 0001 — Differentiation

**Research question:** Can a chemically homogeneous environment develop spatial differentiation without explicit objects?

### Implementation and parameters

Gray–Scott chemistry on a 256×256 periodic lattice; 4,000 steps, seed 42, central 24×24 perturbation and uniform noise. Two fields, substrate U and autocatalyst V. F=0.035, k=0.062, D_U=0.16, D_V=0.08.

### Mathematical model

```math
\begin{gathered}
R=UV^2\\
\Delta U=0.16L(U)-R+0.035(1-U)\\
\Delta V=0.08L(V)+R-0.097V
\end{gathered}
```



### Visualization and observed results

Five magma-colored snapshots at 100, 500, 1000, 2000 and 4000; final mean 0.021376, standard deviation 0.067936, active fraction 7.67%.

### Interpretation and limitations

A single seed and parameter set do not establish robustness. No video in original generation.

### Reproduction and provenance

- [Source](../render.py) · [Workflow](../.github/workflows/render.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44456063725)
- Run from repository root: `python render.py` after installing dependencies specified by the corresponding workflow.

## Generation 0002 — Diversification

**Research question:** Can competing autocatalysts diversify while sharing a resource?

### Implementation and parameters

Adds W, twelve randomly located 12×12 colonies alternating species, 6,000 steps, shared U. W diffuses at 0.065 and decays at 0.094; V uses 0.08 and 0.097.

### Mathematical model

```math
\begin{gathered}
A=UV^2,\quad B=UW^2\\
\Delta U=0.16L(U)-A-B+0.035(1-U)\\
\Delta V=0.08L(V)+A-0.097V\\
\Delta W=0.065L(W)+B-0.094W
\end{gathered}
```

Definitions: $A$ and $B$ are replication contributions.

### Visualization and observed results

24 RGB snapshots every 250 steps; later 512×512 video at 12 fps. Final active V 0.78%, W 69.31%; means 0.002237 and 0.189419.

### Interpretation and limitations

Different kinetics favor W; no symmetric control or seed ensemble.

### Reproduction and provenance

- [Source](../diversification.py) · [Workflow](../.github/workflows/diversification.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44457866021)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44457866021/artifacts/14498143557) (184,246 bytes)
- Run from repository root: `python diversification.py` after installing dependencies specified by the corresponding workflow.

## Generation 0003 — Symmetry breaking

**Research question:** Can spatially heterogeneous conditions support distinct niches?

### Implementation and parameters

Adds fixed periodic habitat H=(sin x+cos y+0.5 sin(2x-y))/2.5. 8,000 steps; sampling every 40.

### Mathematical model

```math
\begin{gathered}
H=\frac{\sin x+\cos y+0.5\sin(2x-y)}{2.5}\\
\lambda_V=0.097+0.009H\\
\lambda_W=0.094-0.009H
\end{gathered}
```

The remaining chemistry is unchanged.

### Visualization and observed results

201 frames at 24 fps, 512×512, habitat image. Final active V 15.95%, W 63.54%; means 0.040929 and 0.168649.

### Interpretation and limitations

Duration also changed relative to G0002; no causal isolation of habitat effect.

### Reproduction and provenance

- [Source](../symmetry.py) · [Workflow](../.github/workflows/symmetry.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44457870135)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44457870135/artifacts/14499105302) (443,751 bytes)
- Run from repository root: `python symmetry.py` after installing dependencies specified by the corresponding workflow.

## Generation 0004 — Dynamics

**Research question:** How does circulation affect spatial organization?

### Implementation and parameters

Adds prescribed time-dependent streamfunction and conservative first-order upwind transport before each chemical update.

### Mathematical model

```math
\begin{gathered}
\psi=2[\sin(x+0.002t)\sin y\\
\qquad+0.5\cos(2x-y-0.002t)]\\
v_x=d_y\psi,\quad v_y=-d_x\psi\\
F_i=\max(v_i,0)A+\min(v_i,0)A_{+i}\\
A'=A+\sum_i(F_{-i}-F_i)
\end{gathered}
```

Here $A_{+i}$ is the adjacent cell value in the positive direction.

### Visualization and observed results

201 frames; final active V 15.33%, W 63.36%; means 0.039153 and 0.161751.

### Interpretation and limitations

Flow is externally prescribed; upwind scheme introduces numerical diffusion.

### Reproduction and provenance

- [Source](../dynamics.py) · [Workflow](../.github/workflows/dynamics.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44457866021)
- Run from repository root: `python dynamics.py` after installing dependencies specified by the corresponding workflow.

## Generation 0005 — Feedback

**Research question:** Can matter alter the flow that transports it?

### Implementation and parameters

Adds relaxing feedback field Q sourced by species imbalance; adds Q to streamfunction and bounds face velocity magnitude.

### Mathematical model

```math
\begin{gathered}
\Delta Q=0.12L(Q)+0.025(V-W-Q)\\
\psi=\psi_{\mathrm{external}}+0.8Q\\
\mathbf v'=\mathbf v\min(1,0.8/\mathrm{CFL})
\end{gathered}
```

CFL denotes the conservative face-speed bound.

### Visualization and observed results

Final active V 14.78%, W 63.87%; flow RMS 0.054196; Q RMS 0.205278. Raw MP4 upload introduced for video generations.

### Interpretation and limitations

Feedback is designed, not a fluid momentum equation; external forcing persists.

### Reproduction and provenance

- [Source](../feedback.py) · [Workflow](../.github/workflows/feedback.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44457878072)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44457878072/artifacts/14498178731)
- Run from repository root: `python feedback.py` after installing dependencies specified by the corresponding workflow.

## Generation 0006 — Volumetric emergence

**Research question:** Can differentiation persist in a volumetric space?

### Implementation and parameters

80³ lattice, 1,800 steps, stride 15, 20 seeded 6³ colonies. H=(sin x+cos y+sin z)/3; diffusion U/V/W=0.12/0.06/0.05. Q diffusion 0.10. Transport confined to xy planes.

### Mathematical model

```math
\begin{gathered}
\Delta Q=0.10L(Q)+0.025(V-W-Q)\\
\psi=0.8Q+0.6\sin(x+0.003t)\sin y\cos z\\
v_x=d_y\psi,\quad v_y=-d_x\psi,\quad v_z=0
\end{gathered}
```

Transport is confined to the xy plane.

### Visualization and observed results

121 frames, 512×512 rotating emission–absorption volume. Final active V 16.53%, W 62.58%, Q RMS 0.203499.

### Interpretation and limitations

Three-dimensional lattice but no z advection; dimensionality, resolution and kinetics changed simultaneously.

### Reproduction and provenance

- [Source](../volume.py) · [Workflow](../.github/workflows/volume.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44557622978)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44557622978/artifacts/14545049041)
- Run from repository root: `python volume.py` after installing dependencies specified by the corresponding workflow.

## Generation 0007 — Circulation

**Research question:** Can flow circulate across all three axes?

### Implementation and parameters

80³, 2,400 steps, stride 12. Three vector-potential components produce full discrete curl. Exact outgoing-face bound limits transport; assert divergence below 1e-5.

### Mathematical model

```math
\begin{gathered}
A_z=0.8Q+0.45\sin(x+0.003t)\sin y\\
A_y=0.6Q+0.45\sin(z-0.002t)\cos x\\
A_x=-0.5Q+0.45\cos(y+0.002t)\sin z\\
\mathbf v=\nabla_d\times\mathbf A,\quad \nabla_d\cdot\mathbf v=0
\end{gathered}
```

The discrete curl uses backward differences.

### Visualization and observed results

201 frames, padded 640×640 camera orbit with trilinear sampling; final active V 12.32%, W 65.97%.

### Interpretation and limitations

Discrete divergence-free transport is not Navier–Stokes; changed camera and duration.

### Reproduction and provenance

- [Source](../circulation.py) · [Workflow](../.github/workflows/circulation.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44558108736)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44558108736/artifacts/14545249000)
- Run from repository root: `python circulation.py` after installing dependencies specified by the corresponding workflow.

## Generation 0008 — Energetics

**Research question:** Can a replenishable local resource constrain replication?

### Implementation and parameters

Adds advected energy field E initialized to 1. Spatial supply S=0.012+0.008(H+1)/2; corrected workflow run includes E transport.

### Mathematical model

```math
\begin{gathered}
A=UV^2E,\quad B=UW^2E\\
S=0.012+0.008(H+1)/2\\
\Delta E=0.10L(E)+S(1-E)-0.10(A+B)
\end{gathered}
```

$S$ denotes local energy supply.

### Visualization and observed results

Energy modulates brightness; final active V 5.23%, W 44.22%; E mean 0.924018, minimum 0.842143; no cells below 0.25.

### Interpretation and limitations

Energy is phenomenological, not thermodynamic; no depletion at chosen parameterization.

### Reproduction and provenance

- [Source](../energetics.py) · [Workflow](../.github/workflows/energetics.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44558657774)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44558657774/artifacts/14545968389)
- Run from repository root: `python energetics.py` after installing dependencies specified by the corresponding workflow.

## Generation 0009 — Organization

**Research question:** Can activity construct a persistent environment?

### Implementation and parameters

Adds stationary matrix M, initialized to zero; matrix reduces local chemical diffusion. Face diffusivity is the arithmetic mean of neighboring coefficients, ensuring conservative fluxes.

### Mathematical model

```math
\begin{gathered}
\Delta M=0.025L(M)+0.12(A+B)(1-M)-0.003M\\
\eta=\frac{1}{1+5M}\\
D_{i+1/2}=\frac{D_i+D_{i+1}}{2}
\end{gathered}
```

$\eta$ multiplies the chemical diffusivities.

### Visualization and observed results

Final active V 5.25%, W 40.78%; M mean 0.295633, active fraction 84.47%, one component. Matrix is rendered in lavender.

### Interpretation and limitations

Connected matrix does not imply autonomous entity; M is anchored, not advected.

### Reproduction and provenance

- [Source](../organization.py) · [Workflow](../.github/workflows/organization.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44560478967)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44560478967/artifacts/14548862348)
- Run from repository root: `python organization.py` after installing dependencies specified by the corresponding workflow.

## Generation 0010 — Communication

**Research question:** Can a locally excitable medium modulate reproduction?

### Implementation and parameters

Adds pulse P and recovery R, initialized to zero with central high-P seed. Signal diffusion is matrix dependent; recovery is a slow local relaxation.

### Mathematical model

```math
\begin{gathered}
T=0.18+0.65R\\
X=P(1-P)\max(P-T,0)\\
I=P\max(T-P,0)\\
J=0.08\operatorname{clip}(4(V+W-0.18),0,1)\\
\Delta P=\mathcal D(P,0.12(0.25+0.75M))\\
\quad+0.35(X-I)+J(1-P)-0.015P\\
\Delta R=0.025(P-R)\\
A=UV^2E(1+0.12P)\\
B=UW^2E(1-0.12P)
\end{gathered}
```

Here $\mathcal D$ denotes heterogeneous diffusion.

### Visualization and observed results

Green signal overlay. Final V 12.93%, W 26.46%, signal active 7.97%, M active 76.19%, six structural components.

### Interpretation and limitations

Nonzero excitation does not prove propagating communication; signal visibility depends on other opacity fields.

### Reproduction and provenance

- [Source](../communication.py) · [Workflow](../.github/workflows/communication.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44561683503)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44561683503/artifacts/14550566760)
- Run from repository root: `python communication.py` after installing dependencies specified by the corresponding workflow.

## Generation 0011 — Adaptation

**Research question:** Can slow local environmental memory alter competitive advantage?

### Implementation and parameters

Adds continuous trait T initialized to 0.5; relaxes toward a function of energy, signal, recovery and species imbalance. Tracks consecutive structural mask Jaccard overlap.

### Mathematical model

```math
\begin{gathered}
T_*=\operatorname{clip}(0.5+0.45(P-R)\\
\quad+0.5(E-0.9)+0.6(V-W),0,1)\\
\Delta T=0.015L(T)+0.008(T_*-T)\\
a=0.24(2T-1)\\
A=UV^2E(1+0.12P+a)\\
B=UW^2E(1-0.12P-a)
\end{gathered}
```

$a$ is local competitive advantage.

### Visualization and observed results

Magenta adaptation overlay. Final V 19.43%, W 27.67%, T mean 0.502806, std 0.084066, range 0.314977–0.683945; Jaccard 0.989651; one component.

### Interpretation and limitations

Environmental memory is not heredity. Empty/empty Jaccard is reported as zero by implementation.

### Reproduction and provenance

- [Source](../adaptation.py) · [Workflow](../.github/workflows/adaptation.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44563259888)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44563259888/artifacts/14550583575)
- Run from repository root: `python adaptation.py` after installing dependencies specified by the corresponding workflow.

## Generation 0012 — Hypervolume

**Research question:** What changes when an additional spatial axis is introduced?

### Implementation and parameters

24⁴ lattice, 331,776 cells, 1,200 steps, stride 8; 20 seeded 4⁴ colonies; nine fields. H=(sin x+cos y+sin z+cos ω)/4. Reduce U/V/W diffusion to 0.085/0.045/0.0375, Q and E diffusion to 0.075, pulse diffusion scale to 0.08.

### Mathematical model

```math
\begin{gathered}
A_{ij}=0.35Q+0.25\sin(x_i+0.003t)\\
\quad\times\cos(x_j-0.002t),\quad i<j\\
v_i\gets v_i+d_jA_{ij}\\
v_j\gets v_j-d_iA_{ij}\\
\sum_i d_i v_i=0
\end{gathered}
```

Each axis pair contributes to velocity; $d_i$ denotes a backward difference.

### Visualization and observed results

151 frames, 640×640, moving interpolated 3D section traverses ω twice. Final V 0% active, W 26.65%, M active 43.58%; two components, largest 144,354 cells; Jaccard 0.979483.

### Interpretation and limitations

Fourth dimension is spatial, not time. Resolution, initialization and kinetics confound dimension comparisons.

### Reproduction and provenance

- [Source](../hypervolume.py) · [Workflow](../.github/workflows/hypervolume.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44564906262)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44564906262/artifacts/14551264078)
- Run from repository root: `python hypervolume.py` after installing dependencies specified by the corresponding workflow.

## Generation 0013 — Entities

**Research question:** Can emerging structures be tracked without adding objects to the physics?

### Implementation and parameters

Retains G0012 equations. Label M>0.2 using face connectivity and union-find across periodic faces. Match consecutive components by greedy IoU; candidate overlap/intersection relative to smaller component >=0.1.

### Mathematical model

```math
\begin{gathered}
\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}\\
\frac{|A\cap B|}{\min(|A|,|B|)}\ge0.1\\
z=\frac1n\sum_{k=1}^{n}e^{2\pi\mathrm{i}x_k/N}\\
c=\frac{N}{2\pi}\arg(z)\pmod N
\end{gathered}
```

The centroid is undefined for $|z|<0.05$.

### Visualization and observed results

Export lineages.json with identities, ages, sizes, centroids, births, splits, merges and disappearances. Final two entities, oldest age 1,152 steps, 46 events. MP4 digest identical to G0012.

### Interpretation and limitations

Identity is a heuristic observation, not biological lineage; merge absorption may appear as disappearance; sampling misses transient events.

### Reproduction and provenance

- [Source](../entities.py) · [Workflow](../.github/workflows/entities.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44566223782)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44566223782/artifacts/14552097868)
- Run from repository root: `python entities.py` after installing dependencies specified by the corresponding workflow.

## Generation 0014 — Observatory

**Research question:** Can instrumentation make a 4D universe easier to interpret?

### Implementation and parameters

Preserves physical equations and tracking. Two simultaneous 3D slices separated by N/2; nearest-neighbor identity labels, interpolated scalar fields. Deterministic hue=(ID×0.61803398875) mod 1.

### Mathematical model

No new physical equation; emission–absorption compositing with identity color blending. Identity timeline displays sampled presence of up to eight longest-observed IDs.

### Visualization and observed results

1280×720 dashboard, 151 frames, live records, recent events and identity timeline; verified raw MP4 332,006 bytes.

### Interpretation and limitations

Timeline is presence, not full genealogy; no trajectory overlay. Views are different slices, not direct same-slice comparison.

### Reproduction and provenance

- [Source](../observatory.py) · [Workflow](../.github/workflows/observatory.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44566910443)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44566910443/artifacts/14551809247)
- Run from repository root: `python observatory.py` after installing dependencies specified by the corresponding workflow.

## Generation 0015 — Evolution

**Research question:** Can reproductive variation be inherited and selected?

### Implementation and parameters

Two variant masses Gv/Gw initialized to half each species; advected and diffused with parent populations. Variant frequency p=G/population; selection s=0.22(2E-1)-0.18P-0.12.

### Mathematical model

```math
\begin{gathered}
p_v=\frac{G_v}{\max(V,10^{-12})},\quad p_w=\frac{G_w}{\max(W,10^{-12})}\\
s=0.22(2E-1)-0.18P-0.12\\
f_0=1-s,\quad f_1=1+s\\
\mu\sim\mathcal U(0.001,0.009)\\
B_1=R_1(1-\mu)+R_0\mu\\
D=2p(1-p)
\end{gathered}
```

Diversity uses pooled local frequency.

### Visualization and observed results

Final W variant 1 frequency 14.03% vs 50% initial; pooled local diversity 0.237235; W active 24.85%, V 0%, 31 lineage events. 720p observer visualizes pooled allele.

### Interpretation and limitations

Continuous population model, not individuals. Near-zero V makes its frequency unreliable (denominator floor); diversity pools species.

### Reproduction and provenance

- [Source](../evolution.py) · [Workflow](../.github/workflows/evolution.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44578335666)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44578335666/artifacts/14557248243)
- Run from repository root: `python evolution.py` after installing dependencies specified by the corresponding workflow.

## Generation 0016 — Genetics

**Research question:** Can linked inherited traits create richer selection dynamics?

### Implementation and parameters

Three binary genes C/K/S for catalytic throughput, energy economy and signal response; eight genotypes per species, sixteen independently transported concentrations replacing two populations. Initialize each at one eighth of parent mass.

### Mathematical model

**Reproductive fitness**

```math
\begin{gathered}
F_g=[1+0.16(2C_g-1)]\\
\quad\times[1+0.18(2K_g-1)(1-E)]\\
\quad\times[1+0.20(2S_g-1)(2P-1)]
\end{gathered}
```

**Energy cost**

```math
Q_g=0.085+0.035C_g-0.025K_g
```

**Mutation operator**

```math
B'_g=(1-3\mu)B_g+\mu\sum_{j=0}^{2}B_{g\oplus 2^j}
```

**Genetic entropy**

```math
H=-\sum_{g=0}^{7}p_g\log_2 p_g
```

The three genes are binary; $p_g$ is pooled genotype frequency, and XOR flips one bit.

### Visualization and observed results

Final C/K/S frequencies 98.21/88.66/37.71%; genotype 110=54.13%, 111=32.93% (C,K,S order); entropy 1.59561 bits vs initial 3. Matrix active 100%, one component; 23 events. 23 independent fields.

### Interpretation and limitations

Fitness is designed; pooled entropy hides species differences. Structural saturation undermines entity differentiation. Structural deposition not genetically controlled yet.

### Reproduction and provenance

- [Source](../genetics.py) · [Workflow](../.github/workflows/genetics.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44592781876)
- [Standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44592781876/artifacts/14563813752)
- Run from repository root: `python genetics.py` after installing dependencies specified by the corresponding workflow.

## Generation 0017 — Ecosystem

**Research question:** Can reciprocal metabolic interactions sustain coexistence and avoid structural saturation?

### Implementation and parameters

Adds two transported metabolites Xv/Xw. Opposite-species metabolite boosts genotype replication, with greater benefit from K=1. Signal gene controls matrix deposition; faster signal-dependent turnover.

### Mathematical model

```math
\begin{gathered}
b_g(X)=0.45\frac{X}{0.12+X}(0.35+0.65K_g)\\
\Delta X_v=0.06L(X_v)+0.18A-0.025X_v\\
\quad-\min(0.12U_w,0.25X_v)\\
\Delta X_w=0.06L(X_w)+0.18B-0.025X_w\\
\quad-\min(0.12U_v,0.25X_w)\\
d_g=0.045+0.065S_g\\
\Delta M=0.025L(M)+\left(\sum_g B_gd_g\right)(1-M)\\
\quad-(0.008+0.012P)M
\end{gathered}
```

Uptake terms $U_v,U_w$ represent bonus-attributed contributions; deposition sums births across both species. Metabolites are also advected.

### Visualization and observed results

25 independent fields, 8,294,400 scalar values; observer maps summed metabolites. Logs include metabolite means and overlap. Verified CI run 44616522872: V active 15.3974%, W active 59.6969%; mean metabolites V/W 0.03118446/0.10123751, overlap 0.01251270; energy mean 0.88738347; genotype entropy 1.44840634 bits; matrix mean 0.11090862, only one cell above 0.2; 25 lineage events. Both species active at endpoint, but coexistence stability and causality untested. [Raw MP4 (342,498 bytes)](https://github.com/interrupt21h/ontogenesis/actions/runs/44616522872/artifacts/14575716178) · [Diagnostics](https://github.com/interrupt21h/ontogenesis/actions/runs/44616522872/artifacts/14575711099).

### Interpretation and limitations

Cross-feeding and turnover changed together; no mass-conserving chemical network or demonstrated mutualism. Need controls with each mechanism disabled independently.

### Reproduction and provenance

- [Source](../ecosystem.py) · [Workflow](../.github/workflows/ecosystem.yml)
- [Successful CI run](https://github.com/interrupt21h/ontogenesis/actions/runs/44616522872)
- Run from repository root: `python ecosystem.py` after installing dependencies specified by the corresponding workflow.

## Generation 0018 — Morphogenesis

Status: CI passed.

### Research question

Can intermediate matrix turnover and selective diffusion across structural gradients support persistent differentiated regions? Parent: G0017. Retain sixteen genotype concentrations, reciprocal metabolites, energy, signal, recovery, adaptation and four-dimensional curl transport. No new independent fields.

### Implementation and parameters

24^4 periodic lattice, seed 42, 4,800 unit steps instead of 1,200; frame every six steps including zero. Matrix decay coefficients reduced from 0.008/0.012 to 0.005/0.006. Conservative face diffusion is attenuated by matrix differences, more strongly for chemical populations than substrate.

### Mathematical model

**Matrix turnover**

```math
\Delta M=0.025L(M)+(M_v+M_w)(1-M)-(0.005+0.006P)M
```

**Selective face permeability**

```math
\begin{gathered}
\eta_i=(1+5M_i)^{-1}\\
D_{ij}=\frac{D_i+D_j}{2}\exp(-\kappa|M_j-M_i|)\\
F_{ij}=D_{ij}(a_j-a_i)
\end{gathered}
```

Here $D_i=D_0\eta_i$, with $\kappa=4$ for genotype concentrations and $\kappa=1$ for substrate. Face fluxes cancel pairwise. Advection and metabolite diffusion remain unchanged, so this is selective diffusion, not an impermeable membrane.

**Four-dimensional boundary measurement**

```math
\begin{gathered}
I_i=\mathbf 1[M_i>0.2]\\
S=\sum_i\sum_{k=1}^{4}|I_i-I_{i+\hat e_k}|\\
V=\sum_i I_i,\qquad r=S/\max(V,1)
\end{gathered}
```

### Visualization and observed results

Pending. 801 unique simulated frames at 24 fps (33.375 seconds), 1280×720, H.264 CRF 27, two full camera orbits and four fourth-axis traversals. FFprobe records actual duration, dimensions and frame count. Raw MP4 uploaded separately. Diagnostics include boundary-face count, boundary per occupied cell, and matrix coverage at thresholds 0.1, 0.15, 0.2, 0.25 and 0.3 alongside existing genetic and lineage metrics.

### Interpretation and limitations

Longer runtime, turnover and permeability change together; compare matched-duration controls before causal claims. Matrix threshold boundaries are not enclosed cavities or functional membranes. No cavity detection implemented. Preserved advection can cross interfaces. A zero boundary count can mean either empty or fully occupied domain; inspect coverage jointly. Runtime budget 90 minutes; actual performance unverified.

### Reproduction and provenance

- [Source](../morphogenesis.py) · [Workflow](../.github/workflows/morphogenesis.yml)
- Run from repository root: `python morphogenesis.py` with Python 3.12, requirements.txt and scipy==1.15.3.
- Actual CI metrics and MP4 link pending.



### Verified CI outcome

CI passed: [run](https://github.com/interrupt21h/ontogenesis/actions/runs/44619535803), [raw MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44619535803/artifacts/14581045352) (1,896,622 bytes). Final matrix coverage 10.504075%, two components, largest 30,576 cells, 36,620 boundary faces, oldest identity 1,500 steps, 760 lineage events, entropy 1.572855 bits.


## Generation 0019 — Compartmentalization

Status: CI passed.

### Research question and parent
Can structural material enclose localized regions, and how do those regions relate to population activity, energy and genetic diversity? Retain all G0018 physical equations, initialization, 24^4 periodic lattice, seed 42 and 4,800 integration steps. Only diagnostic and rendering cadence changes (six to four steps); no new dynamic fields.

### Mathematical model

Define the complement of the structural mask:

```math
C=\{i:M_i\leq0.2\}
```

Label face-connected components of C in the chosen rectangular fundamental domain. Retain components with at least eight cells that touch none of its eight boundary faces. This is a conservative enclosure candidate test, not full toroidal homology: regions crossing the coordinate cut are omitted.

```math
\begin{gathered}
f_C=\frac{\sum_{j\in J}|C_j|}{24^4}\\
\overline E_C=\frac{\sum_{i\in C_*} E_i}{|C_*|},\quad C_*=\bigcup_{j\in J}C_j
\end{gathered}
```

Report candidate count, largest candidate, coverage and mean V/W/E inside candidates (null when empty). Retain G0018 matrix threshold sweep, boundary face count, genotype and lineage diagnostics.

### Visualization and outputs
Replace lower identity timeline panel with three fixed-scale time-series panels: active V/W/matrix coverage, pooled genotype entropy (0–3 bits), candidate coverage (0–1). Retain live entity list, recent events and two rotating sections. All charts include observations through current frame, on a fixed full-run time axis. 1,201 unique frames at 24 fps, expected duration 50.042 s, 1280×720, raw H.264 MP4 and separate diagnostics archive. FFprobe records actual output properties.

### Verified results
Pending. Do not infer valid compartments from topology alone. Candidate detection depends on threshold, minimum size and chosen domain cut; no wrap-invariant cavity detection or functional membrane proof. G0018 is still running at commit time. Increased rendering cadence may increase runtime; 90-minute timeout retained.

### Reproduction
[Source](../compartmentalization.py) · [Workflow](../.github/workflows/compartmentalization.yml). Python 3.12, requirements.txt, scipy==1.15.3; run from root.



### Verified CI outcome

CI passed: [run](https://github.com/interrupt21h/ontogenesis/actions/runs/44624382551), [raw MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44624382551/artifacts/14583640908) (2,408,862 bytes). Final matrix coverage 10.503774%, two components, largest 30,575 cells, 36,620 boundary faces, oldest identity 1,500 steps, 856 lineage events, entropy 1.572855 bits, zero final enclosure candidates. Event count depends on observation cadence; endpoint differences are small numerical differences, not new physical mechanisms.


## Generation 0020 — Topological complexity

Status: committed; CI pending.

### Research question and implementation

Retain G0019 physics, seed 42, 24^4 domain, 4,800 steps and stride four. Replace cut-dependent complement segmentation with periodic face-connected labels. Exclude the largest complement component as a background proxy; report other components of at least eight cells. Equal-size ties use label order, so the background choice is not uniquely translation invariant in ties. Small components may wrap, and no contractibility claim is made.

### Mathematical model

The occupied 4D voxels generate a closed cubical complex with periodic identification. Count unique k-dimensional faces for each orientation by Boolean unions of shifted masks. The Euler characteristic is

```math
\chi=\sum_{k=0}^{4}(-1)^k n_k=n_0-n_1+n_2-n_3+n_4
```

For Betti numbers over a field, the Euler–Poincare relation is

```math
\chi=\sum_{k=0}^{4}(-1)^k\beta_k
```

The implementation computes cell counts and Euler characteristic, not individual Betti numbers. Face connectivity in segmentation differs from closed-cube connectivity at corner contacts. Analytic assertions cover empty complex, one voxel, full periodic torus and a periodic one-axis tube.

### Visualization and results

Retain 1,201 frames at 24 fps, target 50.042 seconds, 720p standalone MP4. Show Euler characteristic in live sidebar and secondary complement coverage in the history chart. Export counts of all five cell dimensions and periodic complement components. Pending CI. No persistent homology, multiscale topology or winding-number detection yet; these are future work.

### Reproduction

[Source](../topology.py) · [Workflow](../.github/workflows/topology.yml). Python 3.12, requirements.txt and scipy==1.15.3. Run from root.




### Verified CI outcome

[Successful run](https://github.com/interrupt21h/ontogenesis/actions/runs/44651857629), [MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44651857629/artifacts/14592383068). Final Euler characteristic 0; cell counts [56148, 200178, 266887, 157706, 34849]; two structural components, one complement component, zero secondary complement candidates, 856 lineage events, entropy 1.572855 bits. Analytic self-tests passed.

## Generation 0021 — Multiscale topological persistence

Status: committed; CI pending.

### Research question and implementation

Do structural features survive changes in the concentration threshold, and do face-connected components wind around the periodic domain? Preserve G0020 physics, seed 42, 24^4 grid, 4800 steps and stride 4. Every 120 integration steps evaluate five thresholds (0.10, 0.15, 0.20, 0.25, 0.30). Label cut-box face components and link opposite faces by directed integer tile translations.

### Mathematical model

For a seam edge from component i to j assign an integer tile displacement. A spanning traversal assigns offsets; nonzero residuals on visited edges identify winding cycles.

```math
r_{ij}=p_i+d_{ij}-p_j\in\mathbb Z^4
```

An axis winds if some cycle residual has a nonzero coordinate on that axis. Record occupied coverage, Euler characteristic, number of face-connected components, winding component count, union of winding axes, and nonwinding complement sizes. The threshold profile is

```math
K_t=\{\text{closed voxels with } M>t\},\quad
\chi(K_t)=\sum_{k=0}^4(-1)^k n_k(t)
```

### Visualization and observed results

Retain G0020 observatory, 1201 frames at 24 fps (50.04 seconds). New threshold diagnostics are in metrics.json at 41 observations including the endpoint. Pending CI. Self-tests distinguish a seam-crossing two-cell blob from a complete periodic tube, and test empty and full domains.

### Interpretation and limitations

This is a multiscale Euler and winding profile, not persistent homology: no feature matching across thresholds, winding subgroup rank or individual Betti numbers are computed. Nonwinding complement components need not be contractible or functional membranes. Closed-cube Euler connectivity differs from face connectivity. No new physical mechanisms are introduced.

### Reproduction and provenance

[Source](../persistence.py) · [Workflow](../.github/workflows/persistence.yml). Python 3.12 and existing dependencies.



## Research priorities

Morphogenesis: investigate selective permeability, localized metabolism and compartment boundaries; measure four-dimensional surface/volume and cavities. Before attributing effects, compare matched-seed controls, disable new mechanisms independently, run parameter sweeps and report uncertainty. No generation establishes consciousness, biological life or autonomous organisms.
