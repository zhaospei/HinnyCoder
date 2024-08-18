if(oConvertUtils.isEmpty(user)){
	user = (LoginUser) SecurityUtils.getSubject().getPrincipal();
}
LogDTO logDTO = new LogDTO(logContent, logType, operatetype, user);
addLog(logDTO);
System.out.println(logType.SIZE);
        System.out.println(this.baseCommonMapper.toString());