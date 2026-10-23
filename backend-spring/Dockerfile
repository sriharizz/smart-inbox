# =============================================================================
# Stage 1: Build JAR with Maven & Java 21
# =============================================================================
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /build

COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn clean package -DskipTests -B

# =============================================================================
# Stage 2: Runtime Image with Eclipse Temurin 21 JRE
# =============================================================================
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends unzip && rm -rf /var/lib/apt/lists/*

# Copy pre-seeded clinical benchmark data & backup archive
COPY data ./data

# Auto-restore 12-case benchmark database if not extracted yet
RUN if [ ! -f data/smartinboxdb.mv.db ] && [ -f data/smartinboxdb-backup.zip ]; then \
        unzip -o data/smartinboxdb-backup.zip -d data/; \
    fi

COPY --from=build /build/target/*.jar app.jar

ENV PORT=8081
EXPOSE 8081

ENTRYPOINT ["sh", "-c", "java -Dserver.port=${PORT:-8081} -jar app.jar"]
