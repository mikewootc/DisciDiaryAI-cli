

# 定义 logger 接口(分等级: debug, info, warn, error)
log_levels = 2 # error: 0, warn: 1, info: 2, debug: 3, trace: 4

class Logger:
    LEVEL_TRACE = 4
    LEVEL_DEBUG = 3
    LEVEL_INFO = 2
    LEVEL_WARN = 1
    LEVEL_ERROR = 0

    def __init__(self, level):
        self.level = level

    def trace(self, *args, **kwargs):
        if self.level >= 4:
            print('\033[02;34m', end='')
            print(*args, **kwargs)
            print('\033[0m', end='')
    
    def debug(self, *args, **kwargs):
        if self.level >= 3:
            print('\033[02;37m', end='')
            print(*args, **kwargs)
            print('\033[0m', end='')
    
    def info(self, *args, **kwargs):
        if self.level >= 2:
            print(*args, **kwargs)
    
    def warn(self, *args, **kwargs):
        if self.level >= 1:
            print('\033[33m', end='')
            print(*args, **kwargs)
            print('\033[0m', end='')
    
    def error(self, *args, **kwargs):
        if self.level >= 0:
            print('\033[31m', end='')
            print(*args, **kwargs)
            print('\033[0m', end='')

    def set_level(self, level):
        self.level = level
    
    # 为了保持向后兼容，仍然支持字典形式调用
    def __getitem__(self, key):
        return getattr(self, key)

logger = Logger(log_levels)

if __name__ == "__main__":
    logger.set_level(4)
    logger.trace("trace message")
    logger.debug("debug message")
    logger.info("info message")
    logger.warn("warn message")
    logger.error("error message")
    logger["debug"]("debug message")