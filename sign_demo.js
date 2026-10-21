/**
 * 前端签名逻辑示意（脱敏版，仅供学习）
 * ------------------------------------------------------------
 * 说明：仅演示「参数串 + 前端 key 做 MD5」这一通用签名模式，
 *       字段名、参数顺序、key 均以占位符表示。
 *       真实签名算法请自行用浏览器 DevTools 定位学习，勿提交。
 */
const crypto = require('crypto');

// 前端硬编码 key，仅参与签名计算，不随请求体发送
const APP_KEY = 'YOUR_APP_KEY';

/** 生成客户端唯一标识（示意实现） */
function genUuid() {
    const ts = Date.now();
    return crypto.createHash('md5').update(String(ts)).digest('hex');
}

/** 通用 MD5 签名 */
function sign(data) {
    return crypto.createHash('md5').update(String(data)).digest('hex');
}

/**
 * 按接口声明的字段顺序拼接参数串，末尾追加 key 后签名
 * @param {Object} params  业务参数（不含 key）
 * @param {string[]} order 接口声明的字段顺序（即 pointParam）
 */
function buildSignString(params, order) {
    const body = order.map(k => `${k}=${params[k]}`).join('&');
    return `${body}&key=${APP_KEY}`;
}

module.exports = { genUuid, sign, buildSignString };

// 使用示例：
// const uuid = genUuid();
// const raw  = buildSignString({ ...params, yduuid: uuid }, ORDER);
// console.log(sign(raw));