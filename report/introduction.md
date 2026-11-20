# Project overview

Ontogenesis studies the emergence of spatial organization in dimensionless, periodically bounded reaction--diffusion systems. The project extends an initial autocatalytic model through feedback, transport, energy, structural memory, signal propagation, heredity, ecological coupling and topology. A generation is a fresh seeded experiment, not a descendant checkpoint. This monograph is regenerated from the version-controlled experimental history.

## Mechanism map

\begin{center}
\begin{tikzpicture}[node distance=7mm, every node/.style={draw=ontoblue,rounded corners,align=center,text width=10cm,minimum height=9mm},>=Latex]
\node (a) {0001--0003: substrate and competing autocatalysts};
\node[below=of a] (b) {0004--0007: transport, feedback and three-dimensional flow};
\node[below=of b] (c) {0008--0011: energy, matrix, signaling and adaptation};
\node[below=of c] (d) {0012--0014: fourth spatial axis, identities and observatory};
\node[below=of d] (e) {0015--0017: inherited variants, genotypes and cross-feeding};
\node[below=of e] (f) {0018--0020: selective interfaces and periodic topology};
\foreach \u/\v in {a/b,b/c,c/d,d/e,e/f}{\draw[->,thick,ontoblue] (\u)--(\v);}
\end{tikzpicture}
\end{center}

The diagram represents the sequence of model revisions, not a biological phylogeny.

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
\begin{axis}[width=.85\linewidth,height=6cm,xlabel={Matrix difference},ylabel={Relative permeability},xmin=0,xmax=1,ymin=0,ymax=1,legend pos=north east,grid=major]
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
\begin{axis}[width=.85\linewidth,height=6cm,ybar,ymin=0,ymax=105,ylabel={Active matrix (percent)},symbolic x coords={G16,G17,G18,G19},xtick=data,bar width=18pt,nodes near coords,nodes near coords style={font=\scriptsize},point meta=y]
\addplot[fill=ontoblue!60,draw=ontoblue] coordinates {(G16,100) (G17,0.0003014) (G18,10.504075) (G19,10.503774)};
\end{axis}
\end{tikzpicture}
\end{center}

Logged final structural coverage at threshold 0.2. G0017 has one occupied cell out of 331,776. This is an endpoint comparison across different models and durations, not a controlled causal experiment.

## Reading the evidence

All historical results are single-seed observations. Active coverage is not mass. Identity events depend on sampling cadence. A successful render establishes execution, not a biological or scientific validation. The report distinguishes analytical examples from measurements and records pending experiments explicitly.
