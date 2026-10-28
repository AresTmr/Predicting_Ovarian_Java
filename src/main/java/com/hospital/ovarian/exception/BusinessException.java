package com.hospital.ovarian.exception;

import lombok.Getter;

@Getter
public class BusinessException extends RuntimeException {

    private final int code;

    public BusinessException(String message) {
        super(message);
        this.code = 400;
    }

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public static BusinessException notFound(String entity) {
        return new BusinessException(404, entity + " 不存在");
    }

    public static BusinessException invalidParam(String field) {
        return new BusinessException(400, "参数不合法: " + field);
    }
}
