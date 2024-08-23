import flute.config.Config;
import org.eclipse.jdt.core.dom.*;

import java.nio.file.*;

// import java.util.Map;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Main {
    public static CompilationUnit parse(String source) {
        ASTParser parser = ASTParser.newParser(AST.getJLSLatest());
        parser.setSource(source.toCharArray());
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        parser.setResolveBindings(true);
        parser.setBindingsRecovery(true);
        parser.setStatementsRecovery(true);
        return (CompilationUnit) parser.createAST(null);
    }

    public static class Visitor extends ASTVisitor {
        private final HashMap<String, List<String>> variables = new HashMap<>();
        private final HashMap<String, String> fields = new HashMap<>();
        private final List<String> methodNames = new ArrayList<>();

        @Override
        public boolean visit(FieldDeclaration node) {
            for (Object fragment : node.fragments()) {
                VariableDeclarationFragment varFragment = (VariableDeclarationFragment) fragment;
                String fieldName = varFragment.getName().getIdentifier();
                String fieldType = node.getType().toString();
                fields.put(fieldName, fieldType);
            }
            return super.visit(node);
        }

        @Override
        public boolean visit(VariableDeclarationFragment node) {
            if (node.getParent() instanceof VariableDeclarationStatement) {
                VariableDeclarationStatement declaration = (VariableDeclarationStatement) node
                        .getParent();
                String variableName = node.getName().getIdentifier();
                String variableType = declaration.getType().toString();
                if (!variables.keySet().contains(variableName)) {
                    variables.put(variableName, new ArrayList<String>());
                }
                variables.get(variableName).add(variableType);
            }
            return super.visit(node);
        }

        @Override
        public boolean visit(SingleVariableDeclaration node) {
            String variableName = node.getName().getIdentifier();
            String variableType = node.getType().toString();
            if (!variables.keySet().contains(variableName)) {
                variables.put(variableName, new ArrayList<String>());
            }
            variables.get(variableName).add(variableType);
            return super.visit(node);
        }

        // If generated code includes static variable usage, may be it already
        // know
        // the context of type that includes the static variable
        // @Override
        // public boolean visit(QualifiedName node) {
        // if (node.getQualifier() instanceof SimpleName) {
        // String typeName = node.getQualifier().toString();
        // String variableName = node.getName().getIdentifier();
        // variables.put(variableName, typeName);
        // }
        // return super.visit(node);
        // }

        @Override
        public boolean visit(MethodInvocation node) {
            methodNames.add(node.getName().getIdentifier());
            return super.visit(node);
        }

        public boolean visit(ClassInstanceCreation node) {

            methodNames.add(node.getType().toString());
            return super.visit(node);
        }

        public List<String> getMethodNames() {
            return methodNames;
        }

        public HashMap<String, List<String>> getVariables() {
            return variables;
        }

        public HashMap<String, String> getFields() {
            return fields;
        }
    }

    public static void main(String[] args) {
        Config.JAVAFX_DIR = "/home/lvdthieu/Token";
        String sourcePath = args[0];
        String methodRawPath = args[1];
        try {
            String source = new String(
                    Files.readAllBytes(Paths.get(sourcePath)));
            CompilationUnit funcCU = parse(source);
            String methodRaw = new String(
                    Files.readAllBytes(Paths.get(methodRawPath)));
            Visitor contentVisitor = new Visitor();
            funcCU.accept(contentVisitor);
            List<String> methodNames = contentVisitor.getMethodNames();
            HashMap<String, List<String>> variables = contentVisitor
                    .getVariables();
            HashMap<String, String> fields = contentVisitor.getFields();
            // Filter method name not in target method
            LinkedHashSet<String> methodNamesInTargetMethod = new LinkedHashSet<>();
            for (String name : methodNames) {
                Pattern pattern = Pattern.compile(name + "\\(");
                Matcher matcher = pattern.matcher(methodRaw);
                if (matcher.find()) {
                    methodNamesInTargetMethod.add(name);
                }
            }

            // Filter variable name not in target method
            LinkedHashSet<String> fieldNamesInTargetMethod = new LinkedHashSet<>();
            LinkedHashSet<String> typeNamesInTargetMethod = new LinkedHashSet<>();
            for (String variableName : variables.keySet()) {
                for (String variableType : variables.get(variableName)) {
                    if (variableType.matches(
                            "(String|int|byte|short|long|float|double|boolean|char|Object|Integer|Long|Double|Boolean|Character|CharSequence|Byte|Float|Long|Short).*")) {
                        continue;
                    }
                    String tmpVariableName = Pattern.quote(variableName);
                    // String tmpVariableType = Pattern.quote(variableType);
                    // Pattern pattern = Pattern.compile("\\b" + tmpVariableType
                    // + "\\s+" + tmpVariableName + "\\b");
                    Pattern pattern = Pattern
                            .compile("\\b" + tmpVariableName + "\\b");
                    Matcher matcher = pattern.matcher(methodRaw);
                    if (matcher.find()) {
                        fieldNamesInTargetMethod.add(variableName);
                        typeNamesInTargetMethod.add(variableType);
                    }
                }
            }
            for (String fieldName : fields.keySet()) {
                String fieldType = fields.get(fieldName);
                if (fieldType.matches(
                        "(String|int|byte|short|long|float|double|boolean|char|Object|Integer|Long|Double|Boolean|Character|CharSequence|Byte|Float|Long|Short).*")) {
                    continue;
                }
                String tmpFieldName = Pattern.quote(fieldName);
                Pattern pattern = Pattern.compile("\\b" + tmpFieldName + "\\b");
                Matcher matcher = pattern.matcher(methodRaw);
                if (matcher.find()) {
                    fieldNamesInTargetMethod.add(fieldName);
                    typeNamesInTargetMethod.add(fieldType);
                }
            }
            System.out.println("<types>");
            for (String type : typeNamesInTargetMethod) {
                System.out.println(type);
            }
            System.out.println("<methods>");
            for (String method : methodNamesInTargetMethod) {
                System.out.println(method);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
