package org.jeecg.modules.base.service.impl;

import com.baomidou.mybatisplus.core.toolkit.IdWorker;
import lombok.extern.slf4j.Slf4j;
import org.apache.shiro.SecurityUtils;
import org.jeecg.common.api.dto.LogDTO;
import org.jeecg.modules.base.mapper.BaseCommonMapper;
import org.jeecg.modules.base.service.BaseCommonService;
import org.jeecg.common.system.vo.LoginUser;
import org.jeecg.common.util.IpUtils;
import org.jeecg.common.util.SpringContextUtils;
import org.jeecg.common.util.oConvertUtils;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.*;

/**
 * @Description: common实现类
 * @author: jeecg-boot
 */
@Service
@Slf4j
public class BaseCommonServiceImpl implements BaseCommonService {

    @Resource
    private BaseCommonMapper baseCommonMapper;

    @Override
    public void addLog(LogDTO logDTO) {
        if(oConvertUtils.isEmpty(logDTO.getId())){
            logDTO.setId(String.valueOf(IdWorker.getId()));
        }
        //保存日志（异常捕获处理，防止数据太大存储失败，导致业务失败）JT-238
        try {
            logDTO.setCreateTime(new Date());
            baseCommonMapper.saveLog(logDTO);
        } catch (Exception e) {
            log.warn(" LogContent length : "+logDTO.getLogContent().length());
            log.warn(e.getMessage());
        }
    }

    @Override
    public void addLog(String logContent, Integer logType, Integer operatetype, LoginUser user) {
        if(oConvertUtils.isEmpty(user)){
            user = (LoginUser) SecurityUtils.getSubject().getPrincipal();
        }
        LogDTO logDTO = new LogDTO(logContent, logType, operatetype, user);
        addLog(logDTO);
    }

    @Override
    public void addLog(String logContent, Integer logType, Integer operateType) {
        addLog(logContent, logType, operateType, null);
    }

    public void demo(Integer logType) {
        System.out.println(logType.SIZE);
        System.out.println(this.baseCommonMapper.toString());
    }

}
