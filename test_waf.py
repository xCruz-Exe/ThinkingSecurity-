from security.waf import WAF

def test_waf():
    waf = WAF(sensitivity=7)
    
    # Test SQLi
    sqli_payload = "SELECT * FROM users WHERE id=1 OR '1'='1'"
    assert waf.inspect_content(sqli_payload) == True
    print("SQLi Test: Passed")
    
    # Test XSS
    xss_payload = "<script>alert('hacked')</script>"
    assert waf.inspect_content(xss_payload) == True
    print("XSS Test: Passed")
    
    # Test Normal
    normal_payload = "Hello world, this is a normal request."
    assert waf.inspect_content(normal_payload) == False
    print("Normal Content Test: Passed")

if __name__ == "__main__":
    test_waf()
