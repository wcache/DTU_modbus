
import sim
import net
import dataCall



def getMisi():
    return sim.getImsi()


def getIccid():
    return sim.getIccid()


def getPhoneNumber():
    return sim.getPhoneNumber()


def csqQueryPoll():
    return net.csqQueryPoll()


def setPDPContext(profileID, ipType, apn, username, password, authType):
    """ 设置APN
    profileID - PDP上下文ID，整型值，范围1~3，一般设置为1。
    ipType - IP协议类型，整型值: 0(IPv4), 1(IPv6), 2(IPv4和IPv6)
    apn - 接入点名称，全称Access Point Name，字符串类型，可为空，为空直接写''，范围0~64字节。
    username - 用户名，字符串类型，可为空，为空直接写''，范围0~64字节。
    password - 密码，字符串类型，可为空，为空直接写''，范围0~64字节。
    authType - APN鉴权方式，整型值，取值范围见下表枚举：0(表示无),1(PAP),2(CHAP),3(PAP和CHAP)

    return: 返回一个整型值，0表示设置成功，-1表示设置失败。
    """
    return dataCall.setPDPContext(profileID, ipType, apn, username, password, authType)
