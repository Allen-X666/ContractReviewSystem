package com.example.contractreview.common;

import java.util.List;

/**
 * 分页响应结果封装类
 *
 * @param <T> 数据类型
 */
public class PageResult<T> {

    /**
     * 当前页码
     */
    private Integer current;

    /**
     * 每页大小
     */
    private Integer size;

    /**
     * 总记录数
     */
    private Long total;

    /**
     * 总页数
     */
    private Long pages;

    /**
     * 数据列表
     */
    private List<T> records;

    /**
     * 是否有下一页
     */
    private Boolean hasNext;

    /**
     * 是否有上一页
     */
    private Boolean hasPrevious;

    public PageResult() {
    }

    public PageResult(Integer current, Integer size, Long total, List<T> records) {
        this.current = current;
        this.size = size;
        this.total = total;
        this.records = records;
        this.pages = (total + size - 1) / size;
        this.hasNext = (long) current < this.pages;
        this.hasPrevious = current > 1;
    }

    /**
     * 构建分页结果
     */
    public static <T> PageResult<T> of(Integer current, Integer size, Long total, List<T> records) {
        return new PageResult<>(current, size, total, records);
    }

    /**
     * 构建空分页结果
     */
    public static <T> PageResult<T> empty(Integer current, Integer size) {
        return new PageResult<>(current, size, 0L, List.of());
    }

    public Integer getCurrent() {
        return current;
    }

    public void setCurrent(Integer current) {
        this.current = current;
    }

    public Integer getSize() {
        return size;
    }

    public void setSize(Integer size) {
        this.size = size;
    }

    public Long getTotal() {
        return total;
    }

    public void setTotal(Long total) {
        this.total = total;
    }

    public Long getPages() {
        return pages;
    }

    public void setPages(Long pages) {
        this.pages = pages;
    }

    public List<T> getRecords() {
        return records;
    }

    public void setRecords(List<T> records) {
        this.records = records;
    }

    public Boolean getHasNext() {
        return hasNext;
    }

    public void setHasNext(Boolean hasNext) {
        this.hasNext = hasNext;
    }

    public Boolean getHasPrevious() {
        return hasPrevious;
    }

    public void setHasPrevious(Boolean hasPrevious) {
        this.hasPrevious = hasPrevious;
    }

    @Override
    public String toString() {
        return "PageResult{" +
                "current=" + current +
                ", size=" + size +
                ", total=" + total +
                ", pages=" + pages +
                ", records=" + records +
                ", hasNext=" + hasNext +
                ", hasPrevious=" + hasPrevious +
                '}';
    }
}
