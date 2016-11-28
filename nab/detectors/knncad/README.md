# KNN-CAD 

if you want to use KNN-CAD algorithm, please make reference to our [article](https://arxiv.org/abs/1608.04585).

This algorithm shows the application of the multi-dimentional conformal anomaly detection on time-series. 

First of all we need to transform time-series into multi-dimensional vectors. We use an approach that is used in the [Singular Spectrum Analysis](https://en.wikipedia.org/wiki/Singular_spectrum_analysis). 

![](https://cloud.githubusercontent.com/assets/5317319/16424389/964ee6e2-3d68-11e6-8cfc-f3e9be9584cf.png)

So we have *L x L* matrix which characterizes time series **X** at time *2L-1*. Сonsideration of the time-series value at time *2L*  consist of the following modification of the matrix *X*:

![](https://cloud.githubusercontent.com/assets/5317319/16424391/96508542-3d68-11e6-9917-9017e134e770.png)

So we have set of *L*-dimentional vectors. Metric on this space based on [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance). Instead of covariance matrix we use its assessment:

![](https://cloud.githubusercontent.com/assets/5317319/16424392/9654e3b2-3d68-11e6-8ff5-6ce7ed8ca51d.png)

Assessment of covariance matrix is computationally expensive operation. In this method we re-assess covariance matrix once per *L/2* time periods.

We used sum of distances to *k* nearest neighbors in matrix *X* as anomaly score for each vector. But this score is not upper bounded. So, we applied [Inductive Conformal Anomaly Detection](https://www.researchgate.net/profile/Goeran_Falkman/publication/258244052_Inductive_conformal_anomaly_detection_for_sequential_detection_of_anomalous_sub-trajectories/links/54fff9910cf2eaf210bccba7.pdf) method with KNN anomaly score as non-conformity measure. The main idea of this method is the following: we have two vector sets -- "training" and "calibration" set. For each vector from calibration set we obtain its anomaly score using training set. We obtain anomaly score for considering vector and after that define normalized anomaly score as relationship between number of vectors from calibration set, whose anomaly score more than anomaly score of considering vector and number of vectors from calibration set:

![](https://cloud.githubusercontent.com/assets/5317319/16424390/964f9736-3d68-11e6-83c0-9c3476bd7ec3.png)

#### Contributors
Vladislav Ishimtsev (ishvlad28@gmail.com)  
Evgeny Burnaev (burnaevevgeny@gmail.com)







