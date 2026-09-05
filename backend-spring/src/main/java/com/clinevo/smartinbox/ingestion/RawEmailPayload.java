package com.clinevo.smartinbox.ingestion;

import java.util.List;

public record RawEmailPayload(
        String filename,
        String messageId,
        String date,
        String sender,
        String senderEmail,
        String recipient,
        String subject,
        String bodyText,
        List<RawAttachmentPayload> attachments,
        byte[] rawBytes
) {}
