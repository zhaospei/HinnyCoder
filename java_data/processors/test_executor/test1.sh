# java -cp $CLOVER com.atlassian.clover.CloverInstr -i clover.db -s src -d build/instr


# Compile instrument file
# mvn dependency:copy-dependencies
# javac -cp $CLOVER:'target/dependency/*' -d bin build/instr/**/*.java


# Compile test file
# javac -cp bin:$JUNIT RegressionTest*.java -d bin


# Run test 
# java -cp bin:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionTest0


# Get report
# java -cp $CLOVER com.atlassian.clover.reporters.html.HtmlReporter -i clover.db -o clover_html


# Run
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/run.py \
#     --input /home/hieuvd/lvdthieu/valid_finetune.parquet \
#     --output /home/hieuvd/lvdthieu/valid_finetune_compiled_3.parquet \
#     --col generated_code \
#     --base-dir /home/hieuvd/lvdthieu/repos/tmp-projects \
#     --log-dir /home/hieuvd/lvdthieu/repos/log2 \
#     --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
#     --proc 30 \
#     --start-end 20:30

# Check
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/run.py \
#     --input /home/hieuvd/lvdthieu/retry_v1.parquet \
#     --output /home/hieuvd/lvdthieu/retry_compiled.parquet \
#     --col generated_code \
#     --base-dir /home/hieuvd/lvdthieu/repos/tmp-projects \
#     --log-dir /home/hieuvd/lvdthieu/repos/log_finetune \
#     --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
#     --proc 4 \
#     --start-end 0:4


# Retry valid left
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/run.py \
#     --input /home/hieuvd/lvdthieu/valid_left.parquet \
#     --output /home/hieuvd/lvdthieu/valid_left_compiled.parquet \
#     --col generated_code \
#     --base-dir /home/hieuvd/lvdthieu/repos/tmp-projects \
#     --log-dir /home/hieuvd/lvdthieu/repos/log_finetune \
#     --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
#     --proc 17 \
#     --start-end 0:17

CLOVER=/home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/lib/clover-4.5.2.jar
JUNIT=/home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/lib/hamcrest-core-1.3.jar:/home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/lib/junit-4.12.jar

DB=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/clover.db
SRC_INSTR=/home/hieuvd/lvdthieu/repos/tmp-projects/88250_symphony/symphony/src
DST_INSTR=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/build/instr
COMPILE_CP="$CLOVER:'/home/hieuvd/lvdthieu/repos/tmp-projects/88250_symphony/symphony/target/dependency/*'"
DST_CP=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/bin
TEST_JAVA=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/RegressionTest0.java
TEST_JAVA_PASS=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/RegressionPassTest0.java
TEST_JAVA_FAIL=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/RegressionFailTest0.java

CLASSPATH=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/classpath.txt
SOURCE=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/sources.txt

CHECK=/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/test_result5.txt

# java -cp $CLOVER com.atlassian.clover.CloverInstr -i $DB -s $SRC_INSTR -d $DST_INSTR
# if [ "$?" -eq 0 ]; then
#     echo "Instrument done"
# fi

# # Collect all dependence class path
# cd /home/hieuvd/lvdthieu/repos/tmp-projects/88250_symphony/symphony
# /home/hieuvd/apache-maven-3.6.3/bin/mvn dependency:build-classpath \
#     -Dmdep.outputFile=$CLASSPATH

# # Find all source file in src folder
# find /home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/build/instr -name "*.java" \
#     >$SOURCE 

# # Run the javac command with the list of source files
# javac -cp $(cat $CLASSPATH):/home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/lib/clover-4.5.2.jar:/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/build/instr \
#     -d /home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/bin \
#     @$SOURCE
# if [ "$?" -eq 0 ]; then
#     echo "Compile instrumented code done"
# fi

# # Run the javac command for test file
# javac -cp $DST_CP:$JUNIT $TEST_JAVA -d $DST_CP
# if [ "$?" -eq 0 ]; then
#     echo "Compile test done"
# fi

# # Run test
# cd $DST_CP
# java -cp $DST_CP:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionTest0 > $CHECK
# if [ "$?" -eq 0 ]; then
#     echo "Run test done"
# fi

# Compile pass and fail test
javac -cp $DST_CP:$JUNIT $TEST_JAVA_PASS $TEST_JAVA_FAIL -d $DST_CP
if [ "$?" -eq 0 ]; then
    echo "Compile pass and fail test done"
fi

java -cp $DST_CP:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionPassTest0 
if [ "$?" -eq 0 ]; then
    echo "Run pass test done"
fi

java -cp $DST_CP:$CLOVER:$JUNIT org.junit.runner.JUnitCore RegressionFailTest0
if [ "$?" -eq 0 ]; then
    echo "Run fail test done"
fi

# # Store test result into clover_html
# java -cp $CLOVER com.atlassian.clover.reporters.html.HtmlReporter -i $DB -o clover_html
# if [ "$?" -eq 0 ]; then
#     echo "Store result done"
# fi

#Test run test
# javac -cp $JUNIT /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/CustomRunListener.java /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/TestRunner.java
# cd /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor
# java -cp $DST_CP:$CLOVER:$JUNIT:.:/home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/bin TestRunner RegressionTest0.class /home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/test_pass.txt /home/hieuvd/lvdthieu/repos/randoop/88250_symphony/symphony/src/main/java/org/b3log/symphony/model/feed/RSSChannel/test_fail.txt
