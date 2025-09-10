# 自动交易回测工具
## 简介
  这是一个自动化回测以及模拟盘交易的工具，用户可以通过配置各种参数来进行回测以及模拟交易。该工具支持策略选择、时间区间设置以及账户信息配置等功能。
# 配置文件
## 全局配置文件示例
```
全局配置：config.json
{
        "lisence": "1",  # 准入许可，联系相关人获取
        "strategy": "inflection_point",  #策略名称(策略文件名)
        "fc_code": "simnow",
        #回测需要配置begin和end
        "begin": "10/7/2025",  # 回测开始时间
        "end": "11/7/2025"  #回测结束时间
        #模拟盘交易需要配置账户和密码
        "account": "test",
        "password": "test"
}
```
## 策略配置文件示例
```
策略配置：config下的yaml
{
        NAME: 'inflection_point'  #策略名称
        MODULE: 'inflection_point'  #  与策略名称一致
        CLASS: 'INFLECTION'  #策略文件的Class名
        INTERVAL: '5min'  #回测间隔周期
        PERIOD: '1min'  #回测数据时间维度
        PARAMETERS:  #策略参数
          smooth_period: 25 
          m: 2 
          slow_ema: 50
          fast_ema: 21
          RR: 2.0
        # Define pairs to monitor
        WATCHLIST: ['ao2509'] #回测合约code集合
}
```
# 策略文件
策略在strategies文件夹下编写，可参考示例策略代码

# 回测或者模拟盘交易
## 安装依赖
```bash
pip install http://www.popper-fintech.com/ls/leopardseek_main-2.0.0.tar.gz
```

## 执行
```bash
执行 Start_virtual_trade.py  Main方法(模拟盘交易)
执行 Start_backtest.py  Main方法(回测)
```
## 结果
### 模拟盘结果
手机端可下载快期app，PC端可下载快期交易系统V3，
登录simnow账户，可进行观察(https://www.simnow.com.cn/static/softwareDownload.action)

### 回测结果
执行结束后，浏览器会自动打开回测结果，可进行观察
