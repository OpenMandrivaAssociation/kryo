Name:		kryo
Version:	2.24.0
Release:	1
Summary:	Fast Java serialization
Group:		Development/Java
License:	BSD-3-Clause
URL:		https://github.com/EsotericSoftware/kryo
# Tag kryo-2.24.0. Vendored lib/*.jar, build/*.jar and compat_reports jars
# are not in this archive. Java sources are stored with LF line endings.
Source0:	https://github.com/EsotericSoftware/kryo/archive/refs/tags/kryo-%{version}.tar.gz#/kryo-%{version}.tar.gz
# JDK 27 removed sun.misc.Cleaner. DirectBuffer.cleaner() returns sun.nio.Cleaner.
Patch0:		kryo-2.24.0-jdk27-cleaner.patch

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(com.esotericsoftware.minlog:minlog)
BuildRequires:	mvn(com.esotericsoftware.reflectasm:reflectasm)
BuildRequires:	mvn(org.objenesis:objenesis)
BuildRequires:	mvn(org.ow2.asm:asm)

%description
Kryo 2.24.0 is the serializer Gradle 9.9.1 strictly pins for the
configuration cache. The coordinate is com.esotericsoftware.kryo:kryo.
Kryo 5 is a different API and does not replace this package.

%prep
%autosetup -n kryo-kryo-%{version} -p1
find . -name '*.jar' -delete

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
mkdir -p classes
find src -name '*.java' > sources.list
# sun.nio and sun.nio.ch are not visible under --release 8, and
# --add-exports is rejected together with -target 8. Class version 53
# is the oldest file format that can name those packages.
javac -source 8 -target 9 -encoding UTF-8 -Xlint:-options \
	--add-exports java.base/sun.nio=ALL-UNNAMED \
	--add-exports java.base/sun.nio.ch=ALL-UNNAMED \
	--add-exports jdk.unsupported/sun.misc=ALL-UNNAMED \
	-cp %{_javadir}/minlog.jar:%{_javadir}/reflectasm.jar:%{_javadir}/objenesis.jar:%{_javadir}/asm.jar \
	-d classes @sources.list
jar cf kryo.jar -C classes .
cat > kryo.pom <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.esotericsoftware.kryo</groupId>
  <artifactId>kryo</artifactId>
  <version>%{version}</version>
  <name>Kryo</name>
  <description>Fast, efficient Java serialization.</description>
  <url>https://github.com/EsotericSoftware/kryo</url>
  <licenses>
    <license>
      <name>BSD-3-Clause</name>
      <url>https://opensource.org/license/bsd-3-clause</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.esotericsoftware.reflectasm</groupId>
      <artifactId>reflectasm</artifactId>
      <version>1.09</version>
    </dependency>
    <dependency>
      <groupId>com.esotericsoftware.minlog</groupId>
      <artifactId>minlog</artifactId>
      <version>1.2</version>
    </dependency>
    <dependency>
      <groupId>org.objenesis</groupId>
      <artifactId>objenesis</artifactId>
      <version>2.1</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact kryo.pom:kryo.jar \
	--file-name kryo \
	--filelist .mfiles

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
JAR=%{buildroot}%{_javadir}/kryo.jar
test -f "$JAR"
mkdir -p check
cat > check/Smoke.java <<'END'
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;

public class Smoke {
	public static void main(String[] args) {
		Output out = new Output(64);
		out.writeInt(42);
		Input in = new Input(out.toBytes());
		int value = in.readInt();
		if (value != 42) {
			throw new AssertionError(value);
		}
		System.out.println("kryo_ok " + value);
	}
}
END
CP="check:$JAR:%{_javadir}/minlog.jar:%{_javadir}/reflectasm.jar:%{_javadir}/objenesis.jar:%{_javadir}/asm.jar"
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
java -cp "$CP" Smoke > check/out.log
cat check/out.log
grep -F -q 'kryo_ok 42' check/out.log

%files -f .mfiles
%doc license.txt README.md
