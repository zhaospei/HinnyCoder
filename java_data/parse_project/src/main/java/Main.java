import flute.config.Config;
import flute.utils.file_processing.FileProcessor;

import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.*;
import org.eclipse.jdt.core.dom.rewrite.ASTRewrite;
// import org.eclipse.jface.text.Document;
// import org.eclipse.text.edits.TextEdit;

import com.google.gson.*;

import java.io.File;
import java.io.OutputStreamWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Writer;
import java.nio.charset.Charset;
import java.nio.file.*;

import java.util.Hashtable;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import java.util.List;
import java.util.ArrayList;

import me.tongfei.progressbar.ProgressBar;

public class Main {
    private static class Visitor extends ASTVisitor {
        private String relativePath;
        private String source;
        private JsonArray classes = new JsonArray();
        // private JsonArray fields = new JsonArray();
        private JsonArray methods = new JsonArray();

        public Visitor(String relativePath, String source) {
            super();
            this.relativePath = relativePath;
            this.source = source;
        }

        @Override
        public boolean visit(TypeDeclaration node) {
            String name = node.getName().getIdentifier();
            int start = node.getStartPosition();
            int end = start + node.getLength();
            JsonObject currentClass = new JsonObject();
            currentClass.addProperty("name", name);
            currentClass.addProperty("start", start);
            currentClass.addProperty("end", end);
            classes.add(currentClass);
            return super.visit(node);
        }

        @Override
        public boolean visit(EnumDeclaration node) {
            String name = node.getName().getIdentifier();
            int start = node.getStartPosition();
            int end = start + node.getLength();
            JsonObject currentClass = new JsonObject();
            currentClass.addProperty("name", name);
            currentClass.addProperty("start", start);
            currentClass.addProperty("end", end);
            classes.add(currentClass);
            return super.visit(node);
        }

        @Override
        public boolean visit(AnnotationTypeDeclaration node) {
            String name = node.getName().getIdentifier();
            int start = node.getStartPosition();
            int end = start + node.getLength();
            JsonObject currentClass = new JsonObject();
            currentClass.addProperty("name", name);
            currentClass.addProperty("start", start);
            currentClass.addProperty("end", end);
            classes.add(currentClass);
            return super.visit(node);
        }
        // @Override
        // public boolean visit(FieldDeclaration node) {
        // // Get the type of the field
        // String type = node.getType().toString();

        // // Get the modifiers of the field
        // String modifiers = "";
        // for (Object modifier : node.modifiers()) {
        // modifiers += modifier.toString() + " ";
        // }
        // modifiers = modifiers.replaceAll("\\s+$", "");

        // for (Object fragment : node.fragments()) {
        // VariableDeclarationFragment varFrag = (VariableDeclarationFragment) fragment;
        // String name = varFrag.getName().toString();
        // JsonObject field = new JsonObject();
        // field.addProperty("relative_path", relativePath);
        // field.addProperty("class", currentClassName);
        // field.addProperty("type", type);
        // field.addProperty("modifiers", modifiers);
        // field.addProperty("name", name);
        // field.addProperty("raw", node.toString());
        // fields.add(field);
        // }
        // return super.visit(node);
        // }

        @Override
        public boolean visit(MethodDeclaration node) {
            JsonObject method = new JsonObject();
            method.addProperty("relative_path", relativePath);
            String name = node.getName().toString();
            method.addProperty("name", name);
            String returnType = node.getReturnType2() != null ? node.getReturnType2().toString() : "void";
            method.addProperty("return_type", returnType);
            String modifiers = "";
            for (Object modifier : node.modifiers()) {
                modifiers += modifier.toString() + ' ';
            }
            modifiers = modifiers.replaceAll("\\s+$", "");
            method.addProperty("modifiers", modifiers);
            JsonArray parameters = new JsonArray();
            for (Object param : node.parameters()) {
                SingleVariableDeclaration paramDecl = (SingleVariableDeclaration) param;
                String paramType = paramDecl.getType().toString();
                String paramName = paramDecl.getName().toString();
                JsonObject paramInfo = new JsonObject();
                paramInfo.addProperty("type", paramType);
                paramInfo.addProperty("name", paramName);
                parameters.add(paramInfo);
            }
            method.add("parameters", parameters);
            String raw = node.toString();
            method.addProperty("raw", raw);
            Block body = node.getBody();
            if (body != null) {
                int start = body.getStartPosition();
                int length = body.getLength();
                String bodyRaw = source.substring(start + 1, start + length - 1);
                method.addProperty("body_raw", bodyRaw);
            } else {
                method.addProperty("body_raw", "null");
            }
            int start = node.getStartPosition();
            int end = start + node.getLength();
            method.addProperty("start", start);
            method.addProperty("end", end);
            methods.add(method);
            return super.visit(node);
        }

        // public JsonArray getFields() {
        // return fields;
        // }

        public JsonArray getMethods() {
            for (int i = 0; i < methods.size(); i++) {
                JsonObject method = (JsonObject) methods.get(i);
                for (int j = 0; j < classes.size(); j++) {
                    JsonObject aclass = (JsonObject) classes.get(j);

                    if (Integer.valueOf(aclass.get("start").toString()) < Integer
                            .valueOf(method.get("start").toString())
                            && Integer.valueOf(aclass.get("end").toString()) > Integer
                                    .valueOf(method.get("end").toString())) {
                        String cString = aclass.get("name").toString().replaceAll("\"", "");
                        method.addProperty("class", cString);
                        break;
                    }
                }
            }
            return methods;
        }
    }

    public static CompilationUnit parse(String source) {
        ASTParser parser = ASTParser.newParser(AST.getJLSLatest());
        parser.setSource(source.toCharArray());
        // parser.setResolveBindings(true);
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        // parser.setBindingsRecovery(true);
        // parser.setStatementsRecovery(true);
        return (CompilationUnit) parser.createAST(null);
    }

    public static class MethodSignatureVisitor extends ASTVisitor {
        private final ASTRewrite rewriter;

        public MethodSignatureVisitor(ASTRewrite rewriter) {
            this.rewriter = rewriter;
        }

        @Override
        public boolean visit(MethodDeclaration node) {
            // Remove the method body to retain only the signature
            rewriter.set(node, MethodDeclaration.BODY_PROPERTY, null, null);
            return super.visit(node);
        }
    }

    public static class MethodSignatureVisitor2 extends ASTVisitor {
        private final ASTRewrite rewriter;

        public MethodSignatureVisitor2(ASTRewrite rewriter) {
            this.rewriter = rewriter;
        }

        @Override
        public boolean visit(MethodDeclaration node) {
            // Remove the method body to retain only the signature
            rewriter.set(node, MethodDeclaration.BODY_PROPERTY, null, null);
            return super.visit(node);
        }

        @Override
        public boolean visit(Javadoc node) {
            rewriter.remove(node, null);
            return false;
        }

        @Override
        public boolean visit(MarkerAnnotation node) {
            rewriter.remove(node, null);
            return false;
        }

        @Override
        public boolean visit(NormalAnnotation node) {
            rewriter.remove(node, null);
            return false;
        }

        @Override
        public boolean visit(SingleMemberAnnotation node) {
            rewriter.remove(node, null);
            return false;
        }

    }

    private static CompilationUnit createCU(String projectName, String projectDir, String file) {
        try {
            Config.autoConfigure(projectName, projectDir);
        } catch (Exception e) {
            Config.JDT_LEVEL = AST.getJLSLatest();
            Config.JAVA_VERSION = "17";
        }
        ASTParser parser = ASTParser.newParser(Config.JDT_LEVEL);
        parser.setResolveBindings(true);
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        parser.setBindingsRecovery(true);
        parser.setStatementsRecovery(true);
        Hashtable<String, String> options = JavaCore.getOptions();
        JavaCore.setComplianceOptions(Config.JAVA_VERSION, options);
        parser.setCompilerOptions(options);
        parser.setEnvironment(Config.CLASS_PATH, Config.SOURCE_PATH, Config.ENCODE_SOURCE, true);
        parser.setUnitName(file);
        parser.setSource(FileProcessor.read(new File(file)).toCharArray());
        CompilationUnit cu = (CompilationUnit) parser.createAST(null);
        return cu;
    }

    // private static JsonArray parseType(CompilationUnit cu, String relativePath,
    // Logger logger) {
    // int numType = cu.types().size();
    // if (numType == 0) {
    // logger.info("The file has no class: " + relativePath);
    // return null;
    // } else {
    // JsonArray result = new JsonArray();
    // for (int i = 0; i < numType; i++) {
    // JsonObject typeInfo = new JsonObject();
    // typeInfo.addProperty("relative_path", relativePath);
    // AbstractTypeDeclaration type = (AbstractTypeDeclaration) cu.types().get(i);
    // typeInfo.addProperty("name", type.getName().toString());
    // String modifiers = "";
    // for (Object modifier : type.modifiers()) {
    // modifiers += modifier.toString() + " ";
    // }
    // modifiers = modifiers.replaceAll("\\s+$", "");
    // typeInfo.addProperty("modifiers", modifiers);
    // ITypeBinding binding = type.resolveBinding();
    // if (binding == null) {
    // typeInfo.addProperty("qualified_name", "<cant_resolve_binding>");
    // } else {
    // typeInfo.addProperty("qualified_name", binding.getQualifiedName());
    // }

    // // Get the superclass name
    // try {
    // TypeDeclaration classType = (TypeDeclaration) type;
    // Type superClassType = classType.getSuperclassType();
    // if (superClassType != null) {
    // typeInfo.addProperty("extend", superClassType.toString());
    // } else {
    // typeInfo.addProperty("extend", "");
    // }
    // String interfaces = "";
    // for (Object interfaceType : classType.superInterfaceTypes()) {
    // interfaces += interfaceType.toString() + ' ';
    // }
    // interfaces = interfaces.replaceAll("\\s+$", "");
    // typeInfo.addProperty("implements", interfaces);
    // } catch (Exception e) {
    // typeInfo.addProperty("extend", "");
    // typeInfo.addProperty("implements", "");
    // }
    // typeInfo.addProperty("raw", type.toString());

    // // Get raw class without method body
    // try {
    // String source = type.toString();
    // CompilationUnit classCU = parse(source);
    // AST ast = classCU.getAST();
    // ASTRewrite rewriter = ASTRewrite.create(ast);
    // MethodSignatureVisitor visitor = new MethodSignatureVisitor(rewriter);
    // classCU.accept(visitor);
    // Document document = new Document(source);
    // TextEdit edits = rewriter.rewriteAST(document, null);
    // edits.apply(document);
    // typeInfo.addProperty("abstract", document.get());
    // // System.out.println("Abstract:");
    // // System.out.println(document.get());
    // // System.out.println("-----------------------------------");
    // } catch (Exception e) {
    // typeInfo.addProperty("abstract", "error");
    // // System.out.println("Abstract: Error");
    // }
    // // Get raw class without method body, javadoc, annotation
    // try {
    // String source = type.toString();
    // CompilationUnit classCU = parse(source);
    // ASTRewrite rewriter2 = ASTRewrite.create(classCU.getAST());

    // MethodSignatureVisitor2 visitor2 = new MethodSignatureVisitor2(rewriter2);
    // classCU.accept(visitor2);
    // Document document2 = new Document(source);
    // TextEdit edits2 = rewriter2.rewriteAST(document2, null);
    // edits2.apply(document2);
    // typeInfo.addProperty("abstract_compact", document2.get());
    // // System.out.println("Abstract compact:");
    // // System.out.println(document2.get());
    // // System.out.println("-----------------------------------");
    // } catch (Exception e) {
    // typeInfo.addProperty("abstract_compact", "error");
    // // System.out.println("Error");
    // }
    // result.add(typeInfo);
    // }
    // return result;
    // }
    // }

    // private static JsonArray parseField(CompilationUnit cu, String relativePath,
    // Logger logger) {
    // Visitor fieldVisitor = new Visitor(relativePath);
    // cu.accept(fieldVisitor);
    // return fieldVisitor.getFields();
    // }

    public static String readFile(String path, Charset encoding) throws IOException {
        byte[] encoded = Files.readAllBytes(Paths.get(path));
        return new String(encoded, encoding);
    }

    private static JsonArray parseMethod(CompilationUnit cu, String relativePath, String source) {
        Visitor methodVisitor = new Visitor(relativePath, source);
        cu.accept(methodVisitor);
        return methodVisitor.getMethods();
    }

    public static void main(String[] args) {

        Config.JAVAFX_DIR = "/home/hieuvd/lvdthieu/javafx-jmods-17.0.10";
        String baseDir = args[0];
        String projectName = args[1];
        String projectDir = baseDir + "/" + projectName;
        String fileExtension = ".java";
        List<String> files = new ArrayList<>();
        try (Stream<Path> walk = Files.walk(Paths.get(projectDir))) {
            files.addAll(walk.filter(p -> Files.isRegularFile(p) && p.toString().endsWith(fileExtension))
                    .map(Path::toString)
                    .collect(Collectors.toList()));
        } catch (Exception e) {
        }
        // JsonArray types = new JsonArray();
        JsonArray methods = new JsonArray();
        // JsonArray fields = new JsonArray();
        // List tmp = new ArrayList();
        // tmp.add("/home/lvdthieu/code-gen/javamelody_javamelody/javamelody/javamelody-core/src/main/java/net/bull/javamelody/PayloadNameRequestWrapper.java");
        // files = tmp;
        if (files.size() > 0) {

            for (String file : ProgressBar.wrap(files, "Parsing")) {
                try {
                    CompilationUnit cu = createCU(projectName, projectDir, file);
                    String relativePath = file.replace(baseDir + '/', "");
                    String source = readFile(file, Charset.forName("UTF-8")).replaceAll("\r\n", "\n");
                    // JsonArray typeInfos = parseType(cu, relativePath, logger);
                    // if (typeInfos != null) {
                    // types.addAll(typeInfos);
                    // }
                    // JsonArray fieldInfos = parseField(cu, relativePath, logger);
                    // if (fieldInfos != null) {
                    // fields.addAll(fieldInfos);
                    // }
                    JsonArray methodInfos = parseMethod(cu, relativePath, source);

                    if (methodInfos != null) {
                        methods.addAll(methodInfos);
                    }
                } catch (Exception e) {

                }

            }
        }
        // try (Writer writer = new OutputStreamWriter(new FileOutputStream(projectName
        // + "_types.json"), "UTF-8")) {
        // Gson gson = new GsonBuilder().create();
        // gson.toJson(types, writer);
        // } catch (Exception e) {
        // logger.severe(e.getMessage());
        // }
        // try (Writer writer = new OutputStreamWriter(new FileOutputStream(projectName
        // + "_fields.json"), "UTF-8")) {
        // Gson gson = new GsonBuilder().create();
        // gson.toJson(fields, writer);
        // } catch (Exception e) {
        // logger.severe(e.getMessage());
        // }

        try (Writer writer = new OutputStreamWriter(new FileOutputStream(projectName
                + "_methods.json"), "UTF-8")) {
            Gson gson = new GsonBuilder().create();
            gson.toJson(methods, writer);
        } catch (Exception e) {

        }

    }
}
