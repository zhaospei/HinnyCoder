// Here are some relevant code fragments from other files of the repo:
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/DiagonalMatrixTest.java
// --------------------------------------------------
//         final double[] d = { -1.2, 3.4, 5 };
//         final DiagonalMatrix m = new DiagonalMatrix(d, false);
//         final DiagonalMatrix p = (DiagonalMatrix) m.copy();
//         for (int i = 0; i < m.getRowDimension(); ++i) {
//             Assert.assertEquals(m.getEntry(i, i), p.getEntry(i, i), 1.0e-20);
//         }
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/MatrixUtilsTest.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/Array2DRowRealMatrixTest.java
// --------------------------------------------------
// 
//         if (!matrix.isSquare()) {
//             throw new NonSquareMatrixException(matrix.getRowDimension(),
//                                                matrix.getColumnDimension());
//         }
//         if (matrix.getRowDimension() != permutation.length) {
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/DiagonalMatrix.java
// --------------------------------------------------
//         } else {
//             MatrixUtils.checkMultiplicationCompatible(this, m);
//             final int nRows = m.getRowDimension();
//             final int nCols = m.getColumnDimension();
//             final double[][] product = new double[nRows][nCols];
//             for (int r = 0; r < nRows; r++) {
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/DiagonalMatrixTest.java
// --------------------------------------------------
// 
//         final double[] d = { -1.2, 3.4, 5 };
//         final DiagonalMatrix m = new DiagonalMatrix(d);
//         for (int i = 0; i < m.getRowDimension(); i++) {
//             for (int j = 0; j < m.getRowDimension(); j++) {
//                 if (i == j) {
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/JacobiPreconditioner.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/RealVector.java
// --------------------------------------------------
//         }
//         for (int i = 0; i < m; i++) {
//             for (int j = 0; j < n; j++) {
//                 product.setEntry(i, j, this.getEntry(i) * v.getEntry(j));
//             }
//         }
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/DiagonalMatrixTest.java
// --------------------------------------------------
// 
//         final double[] d = { -1.2, 3.4, 5 };
//         final DiagonalMatrix m = new DiagonalMatrix(d, false);
//         for (int i = 0; i < m.getRowDimension(); i++) {
//             for (int j = 0; j < m.getRowDimension(); j++) {
//                 if (i == j) {
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/AbstractRealMatrix.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// apache/commons/math3/linear/MatrixUtilsTest.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
//         for (int c = 0; c < m.getColumnDimension(); c++) {
//             double sum = 0;
//             for (int r = 0; r < m.getRowDimension(); r++) {
//                 sum += m.getEntry(r, c);
//             }
//             d[0][c] = sum;
//         }
//         return new Array2DRowRealMatrix(d, false);
//     }
// 
//     /**
//      * @param m Input matrix.
//      * @return the diagonal n-by-n matrix if m is a column matrix or the column
//      * matrix representing the diagonal if m is a n-by-n matrix.
//      */
//     private static RealMatrix diag(final RealMatrix m) {
//         if (m.getColumnDimension() == 1) {
//             final double[][] d = new double[m.getRowDimension()][m.getRowDimension()];
//             for (int i = 0; i < m.getRowDimension(); i++) {
//                 d[i][i] = m.getEntry(i, 0);
//             }
//             return new Array2DRowRealMatrix(d, false);
//         } else {
//             final double[][] d = new double[m.getRowDimension()][1];
//             for (int i = 0; i < m.getColumnDimension(); i++) {
//                 d[i][0] = m.getEntry(i, i);
//             }
//             return new Array2DRowRealMatrix(d, false);
//         }
//     }
// --------------------------------------------------
// the below code fragment can be found in:
// optim/nonlinear/scalar/noderiv/CMAESOptimizer.java
// --------------------------------------------------
// 
// --------------------------------------------------
// Based on above, complete the method body of the class

class CMAESOptimizer
    extends BaseAbstractMultivariateSimpleBoundsOptimizer<MultivariateFunction>
    implements MultivariateOptimizer {
    /**
     * @param m Input matrix
     * @return Matrix representing the element-wise logarithm of m.
     */
    private static RealMatrix log(final RealMatrix m) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                d[r][c] = Math.log(m.getEntry(r, c));
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @return Matrix representing the element-wise square root of m.
     */
    private static RealMatrix sqrt(final RealMatrix m) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                d[r][c] = Math.sqrt(m.getEntry(r, c));
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @return Matrix representing the element-wise square of m.
     */
    private static RealMatrix square(final RealMatrix m) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                double e = m.getEntry(r, c);
                d[r][c] = e * e;
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix 1.
     * @param n Input matrix 2.
     * @return the matrix where the elements of m and n are element-wise multiplied.
     */
    private static RealMatrix times(final RealMatrix m, final RealMatrix n) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                d[r][c] = m.getEntry(r, c) * n.getEntry(r, c);
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix 1.
     * @param n Input matrix 2.
     * @return Matrix where the elements of m and n are element-wise divided.
     */
    private static RealMatrix divide(final RealMatrix m, final RealMatrix n) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                d[r][c] = m.getEntry(r, c) / n.getEntry(r, c);
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @param cols Columns to select.
     * @return Matrix representing the selected columns.
     */
    private static RealMatrix selectColumns(final RealMatrix m, final int[] cols) {
        final double[][] d = new double[m.getRowDimension()][cols.length];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < cols.length; c++) {
                d[r][c] = m.getEntry(r, cols[c]);
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @param k Diagonal position.
     * @return Upper triangular part of matrix.
     */
    private static RealMatrix triu(final RealMatrix m, int k) {
        final double[][] d = new double[m.getRowDimension()][m.getColumnDimension()];
        for (int r = 0; r < m.getRowDimension(); r++) {
            for (int c = 0; c < m.getColumnDimension(); c++) {
                d[r][c] = r <= c - k ? m.getEntry(r, c) : 0;
            }
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @return Row matrix representing the sums of the rows.
     */
    private static RealMatrix sumRows(final RealMatrix m) {
        final double[][] d = new double[1][m.getColumnDimension()];
        for (int c = 0; c < m.getColumnDimension(); c++) {
            double sum = 0;
            for (int r = 0; r < m.getRowDimension(); r++) {
                sum += m.getEntry(r, c);
            }
            d[0][c] = sum;
        }
        return new Array2DRowRealMatrix(d, false);
    }

    /**
     * @param m Input matrix.
     * @return the diagonal n-by-n matrix if m is a column matrix or the column
     * matrix representing the diagonal if m is a n-by-n matrix.
     */
    private static RealMatrix diag(final RealMatrix m) {<FILL_FUNCTION_BODY>}
}


if (m.getColumnDimension() == 1) {
            final double[][] d = new double[m.getRowDimension()][m.getRowDimension()];
            for (int i = 0; i < m.getRowDimension(); i++) {
                d[i][i] = m.getEntry(i, 0);
            }
            return new Array2DRowRealMatrix(d, false);
        } else {
            final double[][] d = new double[m.getRowDimension()][1];
            for (int i = 0; i < m.getColumnDimension(); i++) {
                d[i][0] = m.getEntry(i, i);
            }
            return new Array2DRowRealMatrix(d, false);
        }
    