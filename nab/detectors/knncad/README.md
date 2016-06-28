# KNN-CAD 
This algorithm shows the application of the multi-dimentional conformal anomaly detection on time-series. 

First of all we need to transform time-series into multi-dimensional vectors. We use an approach that is used in the [Singular Spectrum Analysis](https://en.wikipedia.org/wiki/Singular_spectrum_analysis). 

![](https://latex.codecogs.com/png.download?%5Ctext%7BTime-series%3A%20%7D%20%5Ctextbf%7BX%7D%20%3D%20%28x_1%2C%5Cdots%2Cx_n%29.%5C%5C%20%5Ctext%7BLet%20%7D%20L%3A%20%5C%3B%20%281%20%3C%20L%20%3C%20%5Cfrac%7Bn%7D2%29%5Ctext%7B%20---%20%5Ctextit%7Bwindow%20length%7D%7D.%5C%5C%20%5Ctext%7BForm%20matrix%3A%20%7D%5C%5C%5C%5C%20X%20%3D%20%5Cleft%5B%5Cbegin%7Barray%7D%7Bcccc%7D%20x_1%20%26%20x_2%20%26%20%5Ccdots%20%26%20x_L%20%5C%5C%20x_2%20%26%20x_3%20%26%20%5Ccdots%20%26%20x_%7BL+1%7D%20%5C%5C%20%5Cvdots%20%26%20%5Cvdots%20%26%20%5Cddots%20%26%20%5Cvdots%20%5C%5C%20x_L%20%26%20x_%7BL+1%7D%20%26%20%5Ccdots%20%26%20x_%7B2L-1%7D%20%5Cend%7Barray%7D%5Cright%5D)

So we have *L x L* matrix which characterizes time series **X** at time *2L-1*. Сonsideration of the time-series value at time *2L*  consist of the following modification of the matrix *X*:

![](https://latex.codecogs.com/png.download?%5Cleft%5B%5Cbegin%7Barray%7D%7Bcccc%7D%20x_1%20%26%20x_2%20%26%20%5Ccdots%20%26%20x_L%20%5C%5C%20x_2%20%26%20x_3%20%26%20%5Ccdots%20%26%20x_%7BL+1%7D%20%5C%5C%20%5Cvdots%20%26%20%5Cvdots%20%26%20%5Cddots%20%26%20%5Cvdots%20%5C%5C%20x_L%20%26%20x_%7BL+1%7D%20%26%20%5Ccdots%20%26%20x_%7B2L-1%7D%20%5Cend%7Barray%7D%5Cright%5D%20%5Crightarrow%20%5Cleft%5B%5Cbegin%7Barray%7D%7Bcccc%7D%20x_2%20%26%20x_3%20%26%20%5Ccdots%20%26%20x_%7BL+1%7D%20%5C%5C%20x_3%20%26%20x_4%20%26%20%5Ccdots%20%26%20x_%7BL+2%7D%20%5C%5C%20%5Cvdots%20%26%20%5Cvdots%20%26%20%5Cddots%20%26%20%5Cvdots%20%5C%5C%20x_%7BL+1%7D%20%26%20x_%7BL+2%7D%20%26%20%5Ccdots%20%26%20x_%7B2L%7D%20%5Cend%7Barray%7D%5Cright%5D)

So we have set of *L*-dimentional vectors. Metric on this space based on [Mahalanobis distance](https://en.wikipedia.org/wiki/Mahalanobis_distance). Instead of covariance matrix we use its assessment:

![](https://latex.codecogs.com/png.download?dist%28x%2C%20y%29%20%3D%20%5Csqrt%7B%28x-y%29%5ET%28XX%5ET%29%5E%7B-1%7D%28x-y%29%7D)

Assessment of covariance matrix is computationally expensive operation. In this method we re-assess covariance matrix once per *L/2* time periods.

We used sum of distances to *k* nearest neighbors in matrix *X* as anomaly score for each vector. But this score is not upper bounded. So, we applied [Inductive Conformal Anomaly Detection](https://www.researchgate.net/profile/Goeran_Falkman/publication/258244052_Inductive_conformal_anomaly_detection_for_sequential_detection_of_anomalous_sub-trajectories/links/54fff9910cf2eaf210bccba7.pdf) method with KNN anomaly score as non-conformity measure. The main idea of this method is the following: we have two vector sets -- "training" and "calibration" set. For each vector from calibration set we obtain its anomaly score using training set. We obtain anomaly score for considering vector and after that define normalized anomaly score as relationship between number of vectors from calibration set, whose anomaly score more than anomaly score of considering vector and number of vectors from calibration set:

![](https://latex.codecogs.com/png.download?%5Ctextbf%7BInput%3A%20%7D%24test%20vector%20%24z%24%2C%20training%20set%20%24%28x_1%2C...%2Cx_n%29%24%2C%20pre-computed%20anomaly%20scores%20for%20calibration%20set%20%24%28%5Calpha_1%2C...%2C%5Calpha_m%29%24%5C%5C%20%5Ctextbf%7B%5Cindent%20Output%3A%20%7D%20normalized%20anomaly%20score%20%24p%24%5C%5C%20%241%3A%20%5Calpha%20%3D%20%5Csum_%7Bo%20%5Cin%20KNN%28z%2C%20%28x_1%2C...%2Cx_n%29%29%7Ddist%28z%2C%20o%29%24%5C%5C%20%242%3A%20p%20%3D%20%5Cfrac%7B%7Ci%3D1%2C...%2Cm%3A%5C%3B%5Calpha_i%20%3E%20%5Calpha%20%7C%7D%7Bm%7D%24)

#### Results
| Detector | Standard  Profile  | Reward Low FP | Reward Low FN |
|----------|--------------------|---------------|---------------|
| KNN-CAD   | 57.99 | 43.41 | 64.81 |
#### Contributors
Vladislav Ishimtsev (ishvlad28@gmail.com)\
Evgeny Burnaev (burnaevevgeny@gmail.com)







