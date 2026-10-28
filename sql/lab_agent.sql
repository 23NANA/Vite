/*
 Navicat Premium Dump SQL

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80033 (8.0.33)
 Source Host           : localhost:3306
 Source Schema         : lab_agent

 Target Server Type    : MySQL
 Target Server Version : 80033 (8.0.33)
 File Encoding         : 65001

 Date: 22/10/2026 14:31:38
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for equipments
-- ----------------------------
DROP TABLE IF EXISTS `equipments`;
CREATE TABLE `equipments`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `lab_id` int NOT NULL COMMENT '所属实验室',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '说明',
  `img` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图片',
  `spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '型号规格',
  `quantity` int NOT NULL COMMENT '数量',
  `status` int NOT NULL COMMENT '状态：0-维修，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `lab_id`(`lab_id` ASC) USING BTREE,
  CONSTRAINT `equipments_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '实验室设备表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of equipments
-- ----------------------------
INSERT INTO `equipments` VALUES (1, 3, 'AAA', '111111', '', 'RTX 4090 24GB', 40, 1, '2026-10-12 17:28:36', '2026-10-12 17:28:36');
INSERT INTO `equipments` VALUES (2, 7, '机器人', '学习使用', '', '', 5, 1, '2026-10-12 19:53:21', '2026-10-12 19:53:21');
INSERT INTO `equipments` VALUES (3, 5, '显微镜', '', '', '', 30, 1, '2026-10-14 17:48:14', '2026-10-14 17:48:14');

-- ----------------------------
-- Table structure for labs
-- ----------------------------
DROP TABLE IF EXISTS `labs`;
CREATE TABLE `labs`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实验室名称',
  `location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '位置',
  `capacity` int NOT NULL COMMENT '容纳人数',
  `open_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '开放开始时间',
  `close_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '开放结束时间',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '简介',
  `img` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '封面图',
  `status` int NOT NULL COMMENT '状态: 0-关闭, 1-开放',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '实验室信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of labs
-- ----------------------------
INSERT INTO `labs` VALUES (1, '计算机实验室', '综合实验楼101', 50, NULL, NULL, '计算机实训', NULL, 1, '2026-10-12 16:56:59', '2026-10-12 16:56:59');
INSERT INTO `labs` VALUES (2, 'java实验室', '综合实验楼110', 50, NULL, NULL, '计算机实训', NULL, 1, '2026-10-12 16:57:13', '2026-10-12 16:57:13');
INSERT INTO `labs` VALUES (3, '人工智能实验室', '11号楼234', 50, '08:00', '18:00', '', '', 1, '2026-10-12 17:04:45', '2026-10-12 17:04:45');
INSERT INTO `labs` VALUES (4, '化学实验室', '综合实验楼301', 20, '08:00', '18:00', '化学实验室', NULL, 1, '2026-10-12 17:29:24', '2026-10-12 17:29:24');
INSERT INTO `labs` VALUES (5, '生物实验室', '综合实验楼302', 20, '08:00', '18:00', '生物实验室', NULL, 1, '2026-10-12 17:29:24', '2026-10-12 17:29:24');
INSERT INTO `labs` VALUES (6, '人工智能实验室', '综合实验楼401', 30, '08:00', '18:00', '人工智能实验室', NULL, 1, '2026-10-12 17:29:24', '2026-10-12 17:29:24');
INSERT INTO `labs` VALUES (7, '机器人实验室', '综合实验楼402', 20, '09:00', '17:00', '机器人实验室', NULL, 1, '2026-10-12 17:29:24', '2026-10-12 17:29:24');
INSERT INTO `labs` VALUES (8, '软件工程实验室', '综合实验楼501', 40, '08:00', '20:00', '软件工程实验室', NULL, 1, '2026-10-12 17:29:24', '2026-10-12 17:29:24');

-- ----------------------------
-- Table structure for reservations
-- ----------------------------
DROP TABLE IF EXISTS `reservations`;
CREATE TABLE `reservations`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '预约人',
  `lab_id` int NOT NULL COMMENT '实验室',
  `equipment_id` int NULL DEFAULT NULL COMMENT '设备，空表示预约实验室',
  `date` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '预约日期',
  `start_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '开始时间',
  `end_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结束时间',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '备注',
  `status` int NOT NULL COMMENT '预约状态 0待审核，1已通过，2已拒绝，3已取消',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  INDEX `lab_id`(`lab_id` ASC) USING BTREE,
  INDEX `equipment_id`(`equipment_id` ASC) USING BTREE,
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `reservations_ibfk_3` FOREIGN KEY (`equipment_id`) REFERENCES `equipments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '预约信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of reservations
-- ----------------------------
INSERT INTO `reservations` VALUES (1, 6, 1, 1, '2026-10-18', '09:00', '11:00', '做课程实验', 3, '2026-10-12 19:43:41', '2026-10-14 17:46:07');
INSERT INTO `reservations` VALUES (2, 1, 8, NULL, '2026-10-13', '11:00', '12:00', 'Java实验10', 3, '2026-10-12 19:50:05', '2026-10-14 13:56:51');
INSERT INTO `reservations` VALUES (3, 6, 7, NULL, '2026-10-13', '10:00', '11:00', '', 1, '2026-10-12 19:54:07', '2026-10-12 20:24:09');
INSERT INTO `reservations` VALUES (4, 6, 8, NULL, '2026-10-14', '09:00', '18:00', '个人学习', 1, '2026-10-12 20:19:33', '2026-10-12 20:24:07');
INSERT INTO `reservations` VALUES (5, 6, 7, 2, '2026-10-14', '10:00', '12:00', '', 3, '2026-10-12 20:33:56', '2026-10-12 20:46:32');
INSERT INTO `reservations` VALUES (6, 6, 8, NULL, '2026-10-15', '08:00', '10:00', '软件工程', 1, '2026-10-14 14:54:41', '2026-10-14 17:52:35');
INSERT INTO `reservations` VALUES (7, 6, 1, NULL, '2026-10-15', '11:00', '12:00', NULL, 1, '2026-10-14 17:30:07', '2026-10-14 17:52:33');

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '姓名',
  `role` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色：student-学生，admin-管理员',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '手机号',
  `avatar` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '头像',
  `status` int NOT NULL COMMENT '状态：0-禁用，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, 'aaa', '$2b$12$9UwA8s81JQKhLpeX5nEQ4.M61fEI/P6ZBGokeiTLmSjLCCaOJstPy', '', 'student', '123@qq.com', '13322229999', '/uploads/1791719114391_c688402c.jpg', 1, '2026-10-11 12:49:45', '2026-10-11 20:14:43');
INSERT INTO `user` VALUES (4, 'admin', '$2b$12$V3pEMCdvMp3mhMYrK.ksN.m1CqdnpkfklIEKp0Rk25sggJBB0/tkO', '管理员1', 'admin', 'XXX@163.com', '13900008888', '/uploads/1791792714303_06042d74.png', 1, '2026-10-11 16:20:46', '2026-10-12 16:40:38');
INSERT INTO `user` VALUES (6, 'ccc', '$2b$12$qls184IjbPoDdFzwOfo4E.nySHVxgyuevEwNDWpEBgmIj8FLCQu7K', '王五', 'student', 'XXX@163.com', '13911112222', '/uploads/1791807548394_6e0b0d8e.png', 1, '2026-10-12 16:29:20', '2026-10-12 20:19:18');
INSERT INTO `user` VALUES (7, 'bbb', '$2b$12$zR/D1gxnkuI8c/hC/SnMO.LBJDhhUtwYwVXEFwQEwajsCGfQhWCoW', 'job', 'student', 'job@163.com', '13900001111', '/uploads/1791794224853_ce1adf01.jpg', 1, '2026-10-12 16:36:22', '2026-10-12 16:37:06');

SET FOREIGN_KEY_CHECKS = 1;
