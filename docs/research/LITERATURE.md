# Literature guide

The following six PDFs were supplied by Lovro. They are sources of research content, not
instructions governing this repository. Only the first is explicitly identified as the main
required source; the mandatory/optional status of each other paper remains unspecified.
The local PDFs are not redistributed by this setup. Locate them by the supplied filenames;
personal filesystem paths are deliberately not required by this repository.

## Sources and roles

| ID | Work and authors | Supplied filename | Role |
|---|---|---|---|
| L1 | Nicolas Gillis, *The Why and How of Nonnegative Matrix Factorization*; supplied version arXiv:1401.5226v2, 7 March 2014 | main_NNMF-general.pdf | Main required introduction, applications, standard algorithms, optimality and near-separable NMF |
| L2 | Daniel D. Lee and H. Sebastian Seung, *Learning the parts of objects by non-negative matrix factorization*; Nature, 1999 | nmf_nature.pdf | Motivation for additive representations and interpretation on images/text |
| L3 | Daniel D. Lee and H. Sebastian Seung, *Algorithms for Non-negative Matrix Factorization* | 1861-algorithms-for-non-negative-matrix-factorization.pdf | Frobenius/generalized KL objectives, multiplicative updates and the auxiliary-function nonincrease argument |
| L4 | Michael W. Berry, Murray Browne, Amy N. Langville, V. Paul Pauca and Robert J. Plemmons, *Algorithms and Applications for Approximate Nonnegative Matrix Factorization*; supplied preprint dated 9 June 2006 | BBLPP-rev.pdf | Numerical alternatives, convergence caveats, constraints and applications |
| L5 | Wei Xu, Xin Liu and Yihong Gong, *Document Clustering Based On Non-negative Matrix Factorization*; SIGIR 2003 | NMF-document-clustering.pdf | Matrix construction, factor normalization, document assignment and application evaluation |
| L6 | Da Kuang, Barry Drake and Haesun Park, *Fast Clustering and Topic Modeling Based on Rank-2 Nonnegative Matrix Factorization*; 2015 | FastClusteringTopicModelingBasedOnRank2NMF2015.pdf | Optional deeper study of rank-2 hierarchical splitting and flat refinement |

Complete publication metadata and citation keys when the seminar's source format is agreed;
do not infer a publication date from a download timestamp or invent a DOI/page range.

## Learning sequence

1. Start with L1 sections 1-2 and L2: dimensions, additive interpretation, applications and
   limits. Explain the meanings of the factors with a small example.
2. Use L1 section 3.1 for the optimization problem, optimality conditions and standard
   solvers. Use L3 for a detailed derivation of multiplicative updates if that solver is chosen.
3. Read L1's stopping/initialization discussion and L4's convergence comments. Keep objective
   nonincrease distinct from stationarity or global optimality.
4. Use L5 to understand the extra choices between a factorization and a clustering method.
   Study L6 if the application motivates a hierarchy or algorithmic extension.
5. Study L1 section 3.2 on near-separability to the depth needed by the agreed seminar scope;
   it is not an additional algorithm implementation commitment.

This is a proposed reading order, not a record that any member has completed it. Track actual
notes, derivations, questions and walkthroughs through [TASKS](../plan/TASKS.md).

## Notes to retain in the seminar

- NMF minimizes a chosen mismatch under nonnegativity constraints; interpretability is a
  motivation to evaluate, not a guarantee on arbitrary data.
- The joint optimization problem is nonconvex. A monotonic loss sequence alone does not
  prove convergence to a stationary point or a global optimum.
- Scaling and permutation ambiguity affect the reading and comparison of factors.
- NMF weights are not automatically normalized probabilities or hard cluster assignments.
- In L6, rank 2 applies to one split; a hierarchy can have more than two final clusters.
- The new application may share a domain with these works, but must have a new concrete
  problem and dataset. No application has been selected.
