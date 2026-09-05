package com.clinevo.smartinbox.ingestion;

import java.util.List;

public record RawAttachmentPayload(
        String filename,
        String contentType,
        long sizeBytes,
        byte[] bytes
) {}
