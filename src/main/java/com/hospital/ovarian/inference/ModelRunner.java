package com.hospital.ovarian.inference;

/**
 * 模型推理器抽象接口
 * 任何模型后端（ONNX / Python RPC / Mock）都实现此接口
 * 更换模型实现只需改 application.yml 的 spring.profiles.active
 */
public interface ModelRunner {

    /** 加载/初始化模型 */
    void load();

    /** 卸载/关闭模型 */
    void unload();

    /**
     * 推理
     * @param modelName 模型标识 (fsh | lh | hmg)
     * @param staticFeatures 静态特征向量
     * @param dynamicFeatures 动态时序特征 [time, features]
     * @param mask 样本掩码
     * @return 推理结果
     */
    double[] predict(String modelName, float[] staticFeatures, float[][] dynamicFeatures, float[] mask);

    /** 后端标识，用于诊断 */
    String backendId();
}