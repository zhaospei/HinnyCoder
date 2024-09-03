import pandas as pd

df = pd.read_json(path_or_buf="/var/data/lvdthieu/HinnyCoder/java_data/data/dungbt/comparison/rawrag_bamboo_deepseek-coder-6.7b-base_CodeLlama-7b-hf.jsonl", lines=True, orient="records")
df.info()

# origin = pd.read_parquet("/home/thieuluu/HinnyCoder/java_data/data/tmp/adapt_defects4j_filtered_prompt.parquet")
origin = pd.read_parquet("/var/data/lvdthieu/HinnyCoder/java_data/data/tmp/big_move.parquet")

origin.info()

flaw = [
    "AutoLoadCache/autoload-cache-manager/autoload-cache-manager-jedis/src/main/java/com/jarvis/cache/redis/ShardedJedisCacheManager.java",
    "frontend-maven-plugin/frontend-plugin-core/src/main/java/com/github/eirslett/maven/plugins/frontend/lib/ProxyConfig.java",
    "graphhopper/reader-gtfs/src/main/java/com/conveyal/gtfs/model/Calendar.java",
    "javamelody/javamelody-core/src/main/java/net/bull/javamelody/JpaPersistence.java",
    "javamelody/javamelody-core/src/main/java/net/bull/javamelody/JspWrapper.java",
    "javamelody/javamelody-core/src/main/java/net/bull/javamelody/internal/model/CounterStorage.java",
    "javamelody/javamelody-core/src/main/java/net/bull/javamelody/internal/model/SamplingProfiler.java",
    "jitsi/modules/impl/protocol-sip/src/main/java/net/java/sip/communicator/impl/protocol/sip/xcap/model/xcaperror/UniquenessFailureType.java",
    "jitsi/modules/plugin/desktoputil/src/main/java/net/java/sip/communicator/plugin/desktoputil/plaf/SIPCommTabbedPaneEnhancedUI.java",
    "jitsi/modules/util/src/main/java/net/java/sip/communicator/util/Html2Text.java",
    "kafdrop/src/main/java/kafdrop/config/HealthCheckConfiguration.java",
    "kafdrop/src/main/java/kafdrop/config/InterceptorConfiguration.java",
    "kafdrop/src/main/java/kafdrop/config/MessageFormatConfiguration.java",
    "kafdrop/src/main/java/kafdrop/model/TopicPartitionVO.java",
    "logstash-logback-encoder/src/main/java/net/logstash/logback/appender/AsyncDisruptorAppender.java",
    "logstash-logback-encoder/src/main/java/net/logstash/logback/appender/listener/FailureSummaryAppenderListener.java",
    "logstash-logback-encoder/src/main/java/net/logstash/logback/composite/AbstractCompositeJsonFormatter.java",
    "mapstruct/processor/src/main/java/org/mapstruct/ap/internal/model/MapMappingMethod.java",
    "mini-spring/src/main/java/org/springframework/aop/framework/CglibAopProxy.java",
    "mini-spring/src/main/java/org/springframework/core/convert/support/StringToNumberConverterFactory.java",
    "orientdb/server/src/main/java/com/orientechnologies/orient/server/distributed/operation/NodeOperationTask.java",
    "pmd/pmd-java/src/main/java/net/sourceforge/pmd/lang/java/symbols/table/coreimpl/MostlySingularMultimap.java",
    "snowflake/muon-jediterm/src/main/java/com/jediterm/terminal/HyperlinkStyle.java",
    "spring-cloud-gateway/spring-cloud-gateway-server-mvc/src/main/java/org/springframework/cloud/gateway/server/mvc/filter/Bucket4jFilterFunctions.java",
    "truth/core/src/main/java/com/google/common/truth/Correspondence.java",
    "truth/core/src/main/java/com/google/common/truth/Expect.java",
    "truth/core/src/main/java/com/google/common/truth/IterableSubject.java",
    "truth/extensions/proto/src/main/java/com/google/common/truth/extensions/proto/DiffResult.java",
    "truth/extensions/proto/src/main/java/com/google/common/truth/extensions/proto/IterableOfProtosSubject.java",
    "unirest-java/unirest-modules-mocks/src/main/java/kong/unirest/core/Times.java"
]

origin.drop(index=origin[origin["relative_path"].isin(flaw)].index, inplace=True)

df["relative_path"] = df["metadata"].apply(lambda x: '/'.join(x["fpath_tuple"][1:]))
# df["relative_path"] = df["metadata"].apply(lambda x: '/'.join(x["fpath_tuple"]))
df.drop(index=df[df["relative_path"].isin(flaw)].index, inplace=True)
df.sort_values(by="relative_path", ignore_index=True, inplace=True)
origin.sort_values(by="relative_path", ignore_index=True, inplace=True)
print(df['relative_path'][0])
print(origin['relative_path'][0])
print(len(df['relative_path']))
print(len(origin['relative_path']))
print((df["relative_path"] == origin["relative_path"]).value_counts())

mapper = {
    "Chart": "jfree_jfreechart",	
    "Cli": "apache_commons-cli",
    "Closure": "google_closure-compiler",
    "Codec": "apache_commons-codec",
    "Collections": "apache_commons-collections",
    "Compress": "apache_commons-compress",
    "Csv": "apache_commons-csv",
    "Gson": "google_gson",
    "JacksonCore": "FasterXML_jackson-core",
    "JacksonDatabind": "FasterXML_jackson-databind",
    "JacksonXml": "FasterXML_jackson-dataformat-xml",
    "Jsoup": "jhy_jsoup",
    "JxPath": "apache_commons-jxpath",
    "Lang": "apache_commons-lang",
    "Math": "apache_commons-math",
    "Mockito": "mockito_mockito",
    "Time": "JodaOrg_joda-time"
}

def find(value):
    for key in mapper:
        if mapper[key] == value:
            return key
    return None
def clean_output(output):
    cur_bracket = 0
    for idx, c in enumerate(output):
        if c == '{':
            cur_bracket += 1
        elif c == '}':
            cur_bracket -= 1
        
        # print(c, ' ', cur_bracket)
        
        if cur_bracket < 0:
            return output[:idx]
    
    return output
df["proj_name"] = df["metadata"].apply(lambda x: x["task_id"].split('/')[0])
# df["relative_path"] = df["metadata"].apply(lambda x: '/'.join(x["fpath_tuple"][1:]))
# df["relative_path"] = df["metadata"].apply(lambda x: '/'.join(x["fpath_tuple"]))
df["relative_path"] = df["metadata"].apply(lambda x: '/'.join(x["fpath_tuple"][1:]))
# df["project"] = df["proj_name"].apply(lambda x: find(x))
# df["bug_id"] = origin["bug_id"]
# df["testmethods"] = origin["testmethods"]
df["prediction"] = df["choices"].apply(lambda x: clean_output(x[0]["text"]))
df["masked_class"] = origin["masked_class"]
df["func_name"] = df["metadata"].apply(lambda x: x["function_name"])
df["class_name"] = origin["class_name"]
df["ground_truth"] = df["metadata"].apply(lambda x: x["ground_truth"])
df.info()

df.to_json(
    "/var/data/lvdthieu/HinnyCoder/java_data/data/dungbt/comparison/fixed_rawrag_bamboo_deepseek-coder-6.7b-base_CodeLlama-7b-hf.jsonl", 
    lines=True,
    orient="records"
)