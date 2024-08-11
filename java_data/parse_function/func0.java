        double minValue = 0;
        Integer minPos = null;
        for (int i = tableau.getNumObjectiveFunctions(); i < tableau.getWidth() - 1; i++) {
            final double entry = tableau.getEntry(0, i);
            if (entry < minValue) {
                minValue = entry;
                minPos = i;
            }
        }
        return minPos;
    