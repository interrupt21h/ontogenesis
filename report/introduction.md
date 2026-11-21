# What have we gotten ourselves into?

Ontogenesis began as a challenge to build something complicated enough to be interesting, give it room to evolve, and make GitHub Actions do as much of the work as possible. The simulations provide the raw material. The films provide the spectacle. The real ongoing experiment is how far a growing collection of code, jobs, data, and rendering stages can be pushed before someone has to intervene and babysit the machinery.

This is a curiosity-driven computational playground, not a scientific research program. The mathematical mechanisms are implemented and the recorded numerical observations matter, but they are not evidence of biological life or independently validated scientific discoveries. Think of this as an illustrated engineering field journal: what we tried, what the computers produced, and what it took to keep the system running.

## How it started

The initial creative burst unfolded over November 19–20, 2026. The first recorded numerical CI run began at 04:06:58 UTC on November 19; a film-publication milestone was committed at 16:09:07 UTC on November 20, 36 hours, 2 minutes and 9 seconds later. Those are timestamps of recorded milestones, not a count of hours spent working.

I mostly supplied conceptual direction and evaluated the results, particularly their visual character. AI assistance handled much of the mathematical formulation, implementation, debugging, and documentation. I deliberately allowed some of that mathematical complexity to exceed what I could independently derive or verify. This was part of exploring delegated complexity, not a claim of expertise in all the underlying mathematics.

## What is evolving?

There are really three moving targets. First, each numerical simulation updates its own fields according to local rules. Second, successive numbered experiments change the model, its measurements, and the renderers; they are separately initialized runs, not a single evolving organism. Third, the production pipeline itself gets more elaborate as new simulations, films, archives, and reports have to be coordinated.

The images can be compelling, but the pixels are not the whole story. A four-dimensional field must be sectioned or projected to be seen. Camera movement, lighting, and interpolation change the presentation without changing the simulated physics. Numerical records and source revisions are retained to help separate what happened in the arrays from what happened in the rendering.

## What to look for

The early experiments explore patterns and competition. Later ones add transport, resources, structural memory, higher-dimensional views, inherited variation, and ways of measuring what persists. The late experiments investigate whether the observing tools interfere with the simulation, how to characterize structures without relying on a single threshold, and what happens after a localized disturbance.

Failures, saturation, uninteresting outputs, and unexpectedly expensive workflows are all part of the story. A successful CI run does not guarantee a beautiful film, and a beautiful film does not guarantee an interesting numerical result. Both distinctions are worth keeping.

The next sections retain the technical details for readers who want to inspect the machinery rather than simply enjoy the results.

## Numerical foundations

Lattice spacing and integration time step are unity. The discrete Laplacian sums nearest neighbors minus twice the spatial dimension times the center value. Transport uses first-order upwind fluxes; heterogeneous diffusion uses face-averaged coefficients. A prescribed divergence-free velocity is not a momentum-conserving fluid model. Concentrations and energy are dimensionless. Unless stated otherwise, active chemical coverage is the fraction above 0.1 and matrix coverage the fraction above 0.2. Coverage is not mass fraction.

The experiments documented here use seed 42. Single-seed observations establish examples of behavior rather than statistical robustness. Matched controls can isolate selected mechanisms within a fixed experimental configuration, but broader generalization requires ensembles and sensitivity analysis. Overlap-based identities are observational constructs, not biological ancestry.

## Numerical example: periodic transport

\begin{center}
\begin{tikzpicture}[>=Latex]
\foreach \i in {0,1,2,3,4}{\draw[fill=ontoblue!12] (\i,0) rectangle +(0.85,0.85);}
\foreach \i in {0,1,2,3}{\draw[->,thick,ontogreen] (\i+.65,.42)--(\i+1.2,.42);}
\draw[->,thick,ontoamber] (4.5,.9) to[out=90,in=90] (.4,.9);
\node at (2.4,1.8) {Periodic identification};
\node at (2.4,-.45) {Adjacent face fluxes cancel in the global sum};
\end{tikzpicture}
\end{center}

This schematic illustrates conservation of a transported scalar under flux updates, not conservation of the reacting system as a whole.

## Analytical example: selective permeability

\begin{center}
\begin{tikzpicture}
\begin{axis}[width=.85\linewidth,height=5cm,xlabel={Matrix difference},ylabel={Relative permeability},xmin=0,xmax=1,ymin=0,ymax=1,legend pos=north east,grid=major]
\addplot[ontogreen,thick,domain=0:1,samples=100]{exp(-x)};
\addlegendentry{Substrate}
\addplot[ontoamber,thick,domain=0:1,samples=100]{exp(-4*x)};
\addlegendentry{Genotypes}
\end{axis}
\end{tikzpicture}
\end{center}

Calculated from G0018's exponential barrier factor, holding the unattenuated local face diffusivity fixed. At a matrix difference of 0.5 the factors are approximately 0.607 and 0.135.

## Measured example: structural occupancy

\begin{center}
\begin{tikzpicture}
\begin{axis}[width=.85\linewidth,height=5cm,ybar,ymin=0,ymax=105,ylabel={Active matrix (percent)},symbolic x coords={G16,G17,G18,G19},xtick=data,bar width=18pt,nodes near coords,nodes near coords style={font=\scriptsize},point meta=y]
\addplot[fill=ontoblue!60,draw=ontoblue] coordinates {(G16,100) (G17,0.0003014) (G18,10.504075) (G19,10.503774)};
\end{axis}
\end{tikzpicture}
\end{center}

Logged final structural coverage at threshold 0.2. G0017 has one occupied cell out of 331,776. This is an endpoint comparison across different models and durations, not a controlled causal experiment.

## Measured example: a paired environmental disturbance

In G0028, a localized shock is applied to one of two matched four-dimensional simulations. The verified 24⁴ experiment shows a diminishing local energy deficit alongside persistent differences in the final matrix distribution. These results are examined with native-data comparisons in the G0028 chapter. A film of the disturbed universe alone does not establish recovery.
