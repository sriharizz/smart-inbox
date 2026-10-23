package com.clinevo.smartinbox.service;

import com.clinevo.smartinbox.dto.ExtractionResultDto;
import com.clinevo.smartinbox.dto.LiteratureScreenResultDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
public class AiGatewayClient {

    private static final Logger log = LoggerFactory.getLogger(AiGatewayClient.class);
    private static final String CLOUD_FALLBACK_URL = "https://smart-inbox-production.up.railway.app";

    private final RestTemplate restTemplate;
    private volatile String aiServiceUrl;

    public AiGatewayClient(RestTemplate restTemplate,
                           @Value("${smartinbox.ai-service.url:https://smart-inbox-production.up.railway.app}") String configuredUrl) {
        this.restTemplate = restTemplate;

        String url = configuredUrl;
        // If in cloud environment and url is set to loopback, default to Railway cloud URL
        if (url == null || url.isBlank() || url.contains("127.0.0.1") || url.contains("localhost")) {
            boolean isCloud = System.getenv("RAILWAY_ENVIRONMENT") != null
                           || System.getenv("RAILWAY_STATIC_URL") != null
                           || System.getenv("PORT") != null;
            if (isCloud) {
                log.info("Detected cloud environment with loopback AI URL '{}'. Automatically redirecting to cloud AI service: {}", url, CLOUD_FALLBACK_URL);
                url = CLOUD_FALLBACK_URL;
            }
        }

        this.aiServiceUrl = url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
        log.info("AiGatewayClient initialized with target AI URL: {}", this.aiServiceUrl);
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(aiServiceUrl + "/api/v1/health", Map.class);
            return response.getStatusCode().is2xxSuccessful() && "healthy".equals(response.getBody().get("status"));
        } catch (Exception e) {
            log.warn("AI Microservice health check failed on {}: {}", aiServiceUrl, e.getMessage());
            if (!CLOUD_FALLBACK_URL.equals(aiServiceUrl)) {
                try {
                    ResponseEntity<Map> fbResp = restTemplate.getForEntity(CLOUD_FALLBACK_URL + "/api/v1/health", Map.class);
                    if (fbResp.getStatusCode().is2xxSuccessful() && "healthy".equals(fbResp.getBody().get("status"))) {
                        log.info("Flipping AI target URL to cloud fallback: {}", CLOUD_FALLBACK_URL);
                        this.aiServiceUrl = CLOUD_FALLBACK_URL;
                        return true;
                    }
                } catch (Exception ignored) {}
            }
            return false;
        }
    }

    public ExtractionResultDto processEml(String filename, byte[] emlBytes) {
        return processEml(filename, emlBytes, true);
    }

    public ExtractionResultDto processEml(String filename, byte[] emlBytes, boolean freshProcessing) {
        String url = aiServiceUrl + "/api/v1/process-eml?fresh=" + freshProcessing;
        return uploadFile(url, filename, emlBytes, ExtractionResultDto.class);
    }

    public ExtractionResultDto processPdf(String filename, byte[] pdfBytes) {
        String url = aiServiceUrl + "/api/v1/process-pdf";
        return uploadFile(url, filename, pdfBytes, ExtractionResultDto.class);
    }

    public LiteratureScreenResultDto screenLiteraturePdf(String filename, byte[] pdfBytes) {
        String url = aiServiceUrl + "/api/v1/literature/screen-and-split";
        return uploadFile(url, filename, pdfBytes, LiteratureScreenResultDto.class);
    }

    private <T> T uploadFile(String url, String filename, byte[] bytes, Class<T> responseType) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        ByteArrayResource resource = new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
                return filename;
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        try {
            log.info("Calling Python AI Microservice: {} for file {}", url, filename);
            ResponseEntity<T> response = restTemplate.postForEntity(url, requestEntity, responseType);
            return response.getBody();
        } catch (Exception e) {
            log.warn("Call to AI service failed ({}): {}. Attempting fallback to cloud service...", url, e.getMessage());
            if (!url.startsWith(CLOUD_FALLBACK_URL)) {
                try {
                    String fallbackUrl = url.replace(aiServiceUrl, CLOUD_FALLBACK_URL);
                    log.info("Retrying AI call via cloud fallback URL: {}", fallbackUrl);
                    ResponseEntity<T> fbResponse = restTemplate.postForEntity(fallbackUrl, requestEntity, responseType);
                    this.aiServiceUrl = CLOUD_FALLBACK_URL;
                    return fbResponse.getBody();
                } catch (Exception fbEx) {
                    log.error("Cloud AI fallback also failed: {}", fbEx.getMessage());
                }
            }
            log.error("Failed to process document with AI service {}: {}", url, e.getMessage());
            throw new RuntimeException("AI Microservice processing error: " + e.getMessage(), e);
        }
    }
}
