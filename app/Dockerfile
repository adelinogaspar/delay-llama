# syntax=docker/dockerfile:1.7

# =========================
# Stage 1: Build with Maven
# =========================
FROM maven:3.9.11-eclipse-temurin-25 AS build

WORKDIR /app

# Copy pom first for dependency cache
COPY pom.xml .

# Reuse Maven cache between builds
RUN --mount=type=cache,target=/root/.m2 \
    mvn dependency:go-offline

# Copy source
COPY src ./src

# Build jar using same cache
RUN --mount=type=cache,target=/root/.m2 \
    mvn clean package -DskipTests


# =========================
# Stage 2: Runtime image
# =========================
FROM eclipse-temurin:25-jre

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

#ENTRYPOINT ["java", "-jar", "app.jar"]