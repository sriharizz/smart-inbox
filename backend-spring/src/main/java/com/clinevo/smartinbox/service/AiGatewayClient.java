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

    private final RestTemplate restTemplate;
    private final String aiServiceUrl;

    public AiGatewayClient(RestTemplate restTemplate,
                           @Value("${smartinbox.ai-service.url:http://localhost:8000}") String aiServiceUrl) {
        this.restTemplate = restTemplate;
        this.aiServiceUrl = aiServiceUrl.endsWith("/") ? aiServiceUrl.substring(0, aiServiceUrl.length() - 1) : aiServiceUrl;
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(aiServiceUrl + "/api/v1/health", Map.class);
            return response.getStatusCode().is2xxSuccessful() && "healthy".equals(response.getBody().get("status"));
        } catch (Exception e) {
            log.warn("AI Microservice health check failed: {}", e.getMessage());
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
            log.error("Failed to process document with AI service {}: {}", url, e.getMessage());
            throw new RuntimeException("AI Microservice processing error: " + e.getMessage(), e);
        }
    }
}
