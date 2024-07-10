import flute.config.Config;
import flute.utils.file_processing.FileProcessor;

import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.*;

import java.io.File;
import java.util.Hashtable;
import java.util.List;
import java.util.LinkedList;

public class Main {

    public static class ParamTypeVisitor extends ASTVisitor {
        private final String methodName;
        List<String> paramTypes = new LinkedList<>();
        public ParamTypeVisitor(String methodName) {
            this.methodName = methodName;
        }

        @Override
        public boolean visit(TypeDeclaration typeDeclaration) {
            MethodDeclaration[] methods = typeDeclaration.getMethods();
            for (MethodDeclaration method : methods) {
                if (method.getName().getIdentifier().equals(methodName)) {
                    List<?> parameters = method.parameters();
                    for (Object param : parameters) {
                        SingleVariableDeclaration paramDecl = (SingleVariableDeclaration) param;

                        String qualifiedTypeName = paramDecl.getType()
                                .resolveBinding().getQualifiedName();
                        if (!qualifiedTypeName.matches("(java.|int|byte|short|long|float|double|boolean|char).*")) {
                            paramTypes.add(qualifiedTypeName);
                        }
                    }
                }
            }
            return super.visit(typeDeclaration);
        }

        public List<String> getParamTypes() {
            return paramTypes;
        }
    }

    private static CompilationUnit createCU(String projectName,
            String projectDir, String filePath) {
        Config.autoConfigure(projectName, projectDir);
        ASTParser parser = ASTParser.newParser(Config.JDT_LEVEL);
        parser.setResolveBindings(true);
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        parser.setBindingsRecovery(true);
        parser.setStatementsRecovery(true);
        Hashtable<String, String> options = JavaCore.getOptions();
        JavaCore.setComplianceOptions(Config.JAVA_VERSION, options);
        parser.setCompilerOptions(options);
        parser.setEnvironment(Config.CLASS_PATH, Config.SOURCE_PATH,
                Config.ENCODE_SOURCE, true);
        parser.setUnitName(filePath);
        parser.setSource(FileProcessor.read(new File(filePath)).toCharArray());
        CompilationUnit cu = (CompilationUnit) parser.createAST(null);
        return cu;
    }

    private static String extractParentClass(String projectName,
            String projectDir, String filePath, String className) {
        try {
            CompilationUnit cu = createCU(projectName, projectDir, filePath);
            int numClass = cu.types().size();
            if (numClass == 0) {
                return "<no_class>";
            }
            AbstractTypeDeclaration targetClass = null;
            for (int i = 0; i < numClass; i++) {
                AbstractTypeDeclaration type = (AbstractTypeDeclaration) cu
                        .types().get(i);
                if (type.getName().toString().equals(className)) {
                    targetClass = type;
                }
            }
            if (targetClass == null) {
                return "<cant_find_class>";
            }
            if (targetClass instanceof TypeDeclaration) {
                ITypeBinding binding = ((TypeDeclaration) targetClass)
                        .resolveBinding();
                if (binding == null) {
                    return "<cant_resolve_binding>";
                }
                ITypeBinding superClass = binding.getSuperclass();
                if (superClass == null) {
                    return "<super_class_null>";
                }
                String superClassQualifiedName = superClass.getQualifiedName();
                if (superClassQualifiedName.equals("java.lang.Object")) {
                    return "<no_super_class>";
                } else {
                    return superClassQualifiedName;
                }
            } else {
                return "<no_super_class>";
            }
        } catch (Exception e) {
            return "<encounter_error>";
        }
    }

    private static String extractParamTypes(String projectName,
            String projectDir, String filePath, String className,
            String methodName) {
        try {
            CompilationUnit cu = createCU(projectName, projectDir, filePath);
            ParamTypeVisitor paramTypeVisitor = new ParamTypeVisitor(
                    methodName);
            cu.accept(paramTypeVisitor);
            List<String> paramTypes = paramTypeVisitor.getParamTypes();
            if (paramTypes.size() == 0) {
                return "";
            } else {
                String res = "";
                for (int i = 0; i < paramTypes.size() - 1; i++) {
                    res += paramTypes.get(i) + '\n';
                }
                res += paramTypes.get(paramTypes.size() - 1);
                return res;
            }
        } catch (Exception e) {
            return "<encounter_error>";
        }

    }

    public static void main(String[] args) {
        Config.JAVAFX_DIR = "/home/hieuvd/lvdthieu/javafx-jmods-17.0.10";
        String baseDir = args[0];
        String projectName = args[1];
        String relativePath = args[2];
        String className = args[3];
        String methodName = args[4];
        String projectDir = baseDir + "/" + projectName;
        String filePath = projectDir + "/" + relativePath;
        // String parentClass = extractParentClass(projectName, projectDir,
        // filePath, className);
        String paramTypeDeclarations = extractParamTypes(projectName,
                projectDir, filePath, className, methodName);
        System.out.println(paramTypeDeclarations);
    }
}
