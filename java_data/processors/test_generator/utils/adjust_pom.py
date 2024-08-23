import logging
import xml.etree.ElementTree as ET
import subprocess
from tqdm import tqdm


def add_plugin_to_build(pom_file_path, new_plugins):
    # Parse the new plugin XML string

    new_plugin_elements = [
        ET.fromstring(new_plugin) for new_plugin in new_plugins
    ]

    # Function to ensure a tag exists
    def ensure_tag_exists(parent, tag_name):
        tag = parent.find(tag_name)
        if tag is None:
            tag = ET.SubElement(parent, tag_name)
        return tag

    def strip_namespace(element):
        for elem in element.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

    # Parse the original pom.xml
    tree = ET.parse(pom_file_path)
    root = tree.getroot()
    # Strip namespaces from the root and all its descendants
    strip_namespace(root)
    # Ensure <build> and <plugins> tags exist
    build = ensure_tag_exists(root, "build")
    plugins = ensure_tag_exists(build, "plugins")

    # Check if the plugin already exists to avoid duplicates
    for new_plugin_element in new_plugin_elements:
        plugin_exists = any(
            plugin.find("artifactId").text
            == new_plugin_element.find("artifactId").text
            for plugin in plugins.findall("plugin")
        )
        if not plugin_exists:
            plugins.append(new_plugin_element)
        else:
            plugins.append(new_plugin_element)

    # Write the modified tree back to the original file
    tree.write(pom_file_path, encoding="utf-8", xml_declaration=True)
    print("Plugins added successfully!")


def add_dependencies(pom_file_path, new_dependencies):
    new_dependency_elements = [
        ET.fromstring(new_dependency) for new_dependency in new_dependencies
    ]

    # Function to ensure a tag exists
    def ensure_tag_exists(parent, tag_name):
        tag = parent.find(tag_name)
        if tag is None:
            tag = ET.SubElement(parent, tag_name)
        return tag

    def strip_namespace(element):
        for elem in element.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

    # Parse the original pom.xml
    tree = ET.parse(pom_file_path)
    root = tree.getroot()
    # Strip namespaces from the root and all its descendants
    strip_namespace(root)
    # Ensure <dependencies> exist
    dependencies = ensure_tag_exists(root, "dependencies")
    # print(dependencies)
    # Check if the plugin already exists to avoid duplicates
    for new_dependency_element in new_dependency_elements:
        # dependency_exists = any(
        #     dependency.find("artifactId").text
        #     == new_dependency_element.find("artifactId").text
        #     for dependency in dependencies.findall("dependency")
        # )
        # if not dependency_exists:
        #     dependencies.append(new_dependency_element)
        # else:
        #     dependencies.append(new_dependency_element)
        dependencies.append(new_dependency_element)

    # Write the modified tree back to the original file
    tree.write(pom_file_path, encoding="utf-8", xml_declaration=True)


new_plugins = [
    """
<plugin>
    <artifactId>maven-assembly-plugin</artifactId>
    <executions>
        <execution>
            <phase>package</phase>
            <goals><goal>single</goal></goals>
        </execution>
    </executions>
    <configuration>
        <descriptorRefs>
            <descriptorRef>jar-with-dependencies</descriptorRef>
        </descriptorRefs>
    </configuration>
</plugin>
"""
]
new_dependencies = [
    """
<dependency>
<groupId>commons-logging</groupId>
<artifactId>commons-logging</artifactId>
<version>1.1.1</version>
</dependency>
"""
]
base_dir = "/data/hieuvd/lvdthieu/repos/tmp-projects"
# projects = pd.read_csv("/home/hieuvd/lvdthieu/addjustpom.csv")[
#     "left_projects"
# ].tolist()
projects = [
    # "iluwatar_java-design-patterns", 
    "spring-projects_spring-retry",
    "xerial_sqlite-jdbc",
    "spring-io_initializr",
    "spring-cloud_spring-cloud-netflix",
    "RaiMan_SikuliX1",
    "apache_incubator-hugegraph",
    "spring-cloud_spring-cloud-gateway",
    "networknt_light-4j",
    "orientechnologies_orientdb",
    "pmd_pmd"
]
logger = logging.getLogger()
logger.addHandler(logging.FileHandler("add_plugin.log"))
logger.setLevel(logging.INFO)
projects = projects[8:11]
for project in tqdm(projects, total=len(projects), desc="Changing pom"):
    repo = "_".join(project.split("_")[1:])
    path_to_pom = f"{base_dir}/{project}/{repo}/pom.xml"
    add_plugin_to_build(path_to_pom, new_plugins)
    add_dependencies(path_to_pom, new_dependencies)
    cmd = (
        f"cd {base_dir}/{project}/{repo} "
        f"&& /home/hieuvd/apache-maven-3.6.3/bin/mvn clean install -DskipTests -Dcheckstyle.skip -Dgpg.skip -Dlicense.skip"
    )
    # result = run(cmd, shell=True, capture_output=True)
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        logger.error(f"Still can not install {path_to_pom}")
    else:
        logger.info(f"Installed {path_to_pom}")
