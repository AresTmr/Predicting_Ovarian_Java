package com.hospital.ovarian.utils;

public final class SensitiveMasker {

    private SensitiveMasker() {}

    public static String maskCaseNo(String caseNo) {
        if (caseNo == null || caseNo.isEmpty()) return "";
        if (caseNo.length() <= 4) return "***";
        return "***" + caseNo.substring(caseNo.length() - 4);
    }

    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) return "";
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }

    public static String maskIdCard(String idCard) {
        if (idCard == null || idCard.length() < 10) return "";
        return idCard.substring(0, 6) + "****" + idCard.substring(idCard.length() - 4);
    }
}
