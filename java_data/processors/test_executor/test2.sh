#!/bin/zsh
CLOVER=/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/clover-4.5.2.jar
JUNIT=/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/hamcrest-core-1.3.jar:/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/junit-4.12.jar
MVN="/home/hieuvd/apache-maven-3.6.3/bin/mvn"
TEST_DIR=/data/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/
DB="$TEST_DIR/clover.db"
SRC=/data/hieuvd/lvdthieu/repos/tmp-projects/88250_symphony/symphony/src
INSTR="$TEST_DIR/build/instr"
BIN="$TEST_DIR/bin"
TEST_JAVA="$TEST_DIR/RegressionTest0.java"
TEST_JAVA_PASS="$TEST_DIR/RegressionPassTest0.java"
TEST_JAVA_FAIL="$TEST_DIR/RegressionFailTest0.java"
CLASSPATH="$TEST_DIR/classpath.txt"
SOURCE="$TEST_DIR/sources.txt"
TEST_RESULT="$TEST_DIR/test_result.txt"
SEPARATOR="/home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/separate_pass_fail_test.py"
PASS_RESULT=$TEST_DIR/clover_html_pass
FAIL_RESULT=$TEST_DIR/clover_html_fail
# Instrument
java -cp $CLOVER com.atlassian.clover.CloverInstr -i $DB -s $SRC -d $INSTR
if [ "$?" -eq 0 ]; then
    echo "1) Instrument done"
else
    exit 1
fi

# Collect all dependence class path
# Find all source file in src folder
# Compile instrument files
cd "$SRC/.." && $MVN dependency:build-classpath -Dmdep.outputFile=$CLASSPATH && find "$INSTR" -name "*.java" >$SOURCE && javac -cp $(cat $CLASSPATH):"$CLOVER":"$INSTR" -d "$BIN" @$SOURCE
if [ "$?" -eq 0 ]; then
    echo "2) Compile instrumented code done"
else
    exit 2
fi

# Compile test file
javac -cp $BIN:$JUNIT $TEST_JAVA -d $BIN
if [ "$?" -eq 0 ]; then
    echo "3) Compile test done"
else
    exit 3
fi

# Run test
cd $BIN && java -cp .:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionTest0 > $TEST_RESULT
if [ "$?" -eq 0 ]; then
    echo "4) Run test done"
else
    echo exit 4
fi
# Remove clover.db...
cd $TEST_DIR && rm -rf clover.db[!.]*
if [ "$?" -eq 0 ]; then
    echo "5) Remove tmp clover.db done"
else
    exit 5
fi
# Generate pass and fail te/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannelst
python $SEPARATOR \
    --result $TEST_RESULT \
    --all $TEST_JAVA \
    --pass $TEST_JAVA_PASS \
    --fail $TEST_JAVA_FAIL 
if [ "$?" -eq 0 ]; then
    echo "6) Generate pass and fail test done"
else
    exit 6
fi

# Compile pass and fail test
javac -cp $BIN:$JUNIT $TEST_JAVA_PASS $TEST_JAVA_FAIL -d $BIN
if [ "$?" -eq 0 ]; then
    echo "7) Compile pass and fail test done"
else
    exit 7
fi

# Run pass test
java -cp $BIN:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionPassTest0 
if [ "$?" -eq 0 ]; then
    echo "8) Run pass test done"
else
    exit 8
fi

# Generate clover_html for pass test
java -cp $CLOVER com.atlassian.clover.reporters.html.HtmlReporter -i $DB -o $PASS_RESULT
if [ "$?" -eq 0 ]; then
    echo "9) Store result for pass test done"
else
    exit 9
fi

# Remove clover.db...
cd $TEST_DIR && rm -rf clover.db[!.]*
if [ "$?" -eq 0 ]; then
    echo "10) Remove tmp clover.db done"
else
    exit 10
fi

# Run fail test
java -cp $BIN:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionFailTest0
if [ "$?" -eq 0 ]; then
    echo "11) Run fail test done"
else 
    echo exit 11
fi

# Generate clover_html for fail test
java -cp $CLOVER com.atlassian.clover.reporters.html.HtmlReporter -i $DB -o $FAIL_RESULT
if [ "$?" -eq 0 ]; then
    echo "12) Store result for fail test done"
else 
    exit 12
fi

# Remove clover.db...
cd $TEST_DIR && rm -rf clover.db*
if [ "$?" -eq 0 ]; then
    echo "13) Remove tmp clover.db done"
else
    exit 13
fi
